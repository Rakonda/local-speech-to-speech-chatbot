import io
import json
import os
import queue
import sys
import threading
import wave
import logging

import sounddevice as sd
import soundfile as sf
from gpt4all import GPT4All
from piper.voice import PiperVoice
from vosk import KaldiRecognizer, Model

# === CONFIGURATION ===
def get_from_env(varname, default):
    return os.environ.get(varname, default)

VOSK_MODEL_PATH = get_from_env("VOSK_MODEL_PATH", "vosk-models/vosk-model-en-us-0.22")
MODEL_NAME = get_from_env("MODEL_NAME", "Phi-3 Mini Instruct")
PIPER_MODEL_PATH = get_from_env("PIPER_MODEL_PATH", "piper-voice/en_US-libritts-high.onnx")
GPT4ALL_MODEL_PATH = get_from_env("GPT4ALL_MODEL_PATH", "gguf-models/Phi-3-mini-4k-instruct-q4.gguf")
SYSTEM_PROMPT = get_from_env("SYSTEM_PROMPT", "You are Emma: sarcastic, witty, sometimes dark-humored assistant who secretly flirts with Pedro, Keep responses short: 1-2 sentences max.")
VOSK_SAMPLE_RATE = int(get_from_env("VOSK_SAMPLE_RATE", 16000))
MIN_WORDS = int(get_from_env("MIN_WORDS", 2))
AUDIO_BLOCKSIZE = int(get_from_env("AUDIO_BLOCKSIZE", 8000))
AUDIO_DTYPE = get_from_env("AUDIO_DTYPE", "int16")
AUDIO_CHANNELS = int(get_from_env("AUDIO_CHANNELS", 1))
MIC_QUEUE_MAXSIZE = int(get_from_env("MIC_QUEUE_MAXSIZE", 150))
AUDIO_QUEUE_MAXSIZE = int(get_from_env("AUDIO_QUEUE_MAXSIZE", 10))

# --- Local GPT4All Chat Class ---
class LocalGPT4AllChat:
    def __init__(
        self,
        model_path,
        device=None,
        system_prompt=SYSTEM_PROMPT,
        voice=None,
        audio_queue=None,
    ):
        self.model = GPT4All(model_path, device=device)
        self.system_prompt = system_prompt
        self.chat_history = [{"role": "system", "content": self.system_prompt}]
        self.voice = voice
        self.audio_queue = audio_queue

    def _format_history(self):
        prompt = ""
        for msg in self.chat_history:
            if msg["role"] == "system":
                prompt += f"{msg['content']}\n"
            elif msg["role"] == "user":
                prompt += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n"
        prompt += "Assistant: "
        return prompt

    def ask_stream(self, user_message, max_tokens=100, max_chunk_tokens=30):
        """Stream tokens and speak asynchronously for natural flow."""
        if not self.voice or not self.audio_queue:
            raise ValueError(
                "Voice or audio queue not initialized in LocalGPT4AllChat."
            )

        self.chat_history.append({"role": "user", "content": user_message})
        prompt = self._format_history()

        print("💬 Emma (streaming): ", end="", flush=True)
        buffer = []
        reply_text = ""
        end_marks = {".", "!", "?", "\n"}

        with self.model.chat_session():
            response_generator = self.model.generate(
                prompt,
                max_tokens=max_tokens,
                temp=0.9,
                top_k=40,
                top_p=0.9,
                streaming=True,
            )

            for token in response_generator:
                print(token, end="", flush=True)
                reply_text += token
                buffer.append(token)

                buffer_text = "".join(buffer).strip()
                if (len(buffer) >= max_chunk_tokens) or any(
                    p in buffer_text for p in end_marks
                ):
                    if buffer_text:
                        speak_async(buffer_text, self.voice, self.audio_queue)
                    buffer = []

        if buffer:
            buffer_text = "".join(buffer).strip()
            if buffer_text:
                speak_async(buffer_text, self.voice, self.audio_queue)

        print()
        self.chat_history.append({"role": "assistant", "content": reply_text})
        return reply_text


# --- Piper speaking to audio queue ---
def speak_async(text, voice, audio_queue):
    """
    Generate speech from input text via PiperVoice and put resulting audio data into audio_queue.
    Uses in-memory buffer (BytesIO) for I/O instead of writing to temp files.
    """
    with io.BytesIO() as buf:
        with wave.open(buf, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        buf.seek(0)
        data, sr = sf.read(buf)
    audio_queue.put((data, sr))


# --- Threaded audio playback ---
def play_audio_loop(audio_queue):
    """
    Loop to play back queued audio (asynchronously in a thread).
    Handles KeyboardInterrupt for graceful shutdown.
    """
    while True:
        try:
            data, sr = audio_queue.get()
            sd.play(data, sr)
            sd.wait()
        except queue.Empty:
            logging.warning("Audio playback queue was unexpectedly empty.")
        except KeyboardInterrupt:
            break
        except Exception as e:
            logging.error(f"Unexpected error in play_audio_loop: {e}")


# --- Load models ---
def load_piper_voice(path):
    """Load and return a PiperVoice model from disk, else exit."""
    logging.info("Loading Piper voice model...")
    try:
        return PiperVoice.load(path)
    except Exception as e:
        logging.error(f"Error loading Piper model: {e}")
        sys.exit(1)


def load_vosk_model(path, samplerate):
    """Load and return a Vosk speech-to-text model, else exit."""
    logging.info("Loading Vosk model...")
    try:
        model = Model(path)
        recognizer = KaldiRecognizer(model, samplerate)
        return recognizer
    except Exception as e:
        logging.error(f"Error loading Vosk model: {e}")
        sys.exit(1)


def load_gpt4all_model(voice, audio_queue):
    """Load and return a GPT4All chat wrapper instance, else exit."""
    logging.info(f"Loading GPT4All model: {GPT4ALL_MODEL_PATH}")
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(GPT4ALL_MODEL_PATH):
        logging.error(
            f"ERROR: GPT4All model file not found at {GPT4ALL_MODEL_PATH}\nDownload a .gguf model and update the path."
        )
        sys.exit(1)
    return LocalGPT4AllChat(
        os.path.join(PROJECT_DIR, GPT4ALL_MODEL_PATH),
        system_prompt=SYSTEM_PROMPT,
        voice=voice,
        audio_queue=audio_queue,
    )


# --- Vosk audio callback ---
def audio_callback(indata, frames, time, status, mic_queue):
    """
    Callback for sounddevice input. Puts microphone audio frames into mic_queue for Vosk.
    Handles queue full gracefully.
    """
    if status:
        logging.warning(status)
    try:
        mic_queue.put(bytes(indata), block=False)
    except queue.Full:
        logging.warning("Microphone audio queue is full. Dropping block.")


# --- Main chat loop ---
def run_voice_chat():
    """
    Main function: captures microphone audio, recognizes speech-to-text, generates response,
    and manages audio playback. Runs until interrupted.
    """
    mic_queue = queue.Queue(maxsize=MIC_QUEUE_MAXSIZE)  # For Vosk microphone audio
    audio_queue = queue.Queue(maxsize=AUDIO_QUEUE_MAXSIZE)  # For Piper TTS audio

    threading.Thread(target=play_audio_loop, args=(audio_queue,), daemon=True).start()

    voice = load_piper_voice(PIPER_MODEL_PATH)
    recognizer = load_vosk_model(VOSK_MODEL_PATH, VOSK_SAMPLE_RATE)
    gpt4all_chat = load_gpt4all_model(voice, audio_queue)

    print("🎤 Start chatting... (Ctrl+C to stop)")
    speak_async("Hello Pedro", voice, audio_queue)

    with sd.RawInputStream(
        samplerate=VOSK_SAMPLE_RATE,
        blocksize=AUDIO_BLOCKSIZE,
        dtype=AUDIO_DTYPE,
        channels=AUDIO_CHANNELS,
        callback=lambda indata, frames, time, status: audio_callback(
            indata, frames, time, status, mic_queue
        ),
    ):
        while True:
            try:
                data = mic_queue.get()  # <-- use mic_queue here
                if recognizer.AcceptWaveform(data):
                    recognizer.SetWords(True)
                    recognizer.SetPartialWords(True)
                    res = json.loads(recognizer.Result())
                    user_text = res.get("text", "").strip()
                    word_count = len(user_text.split())

                    if user_text and word_count >= MIN_WORDS:
                        print(f"\nYou said: {user_text}")
                        print("💬 Generating streaming response ...")
                        gpt4all_chat.ask_stream(user_text)
                        print("💬 You can speak now!")
            except KeyboardInterrupt:
                print("\nExiting…")
                break
            except queue.Empty:
                logging.warning("Mic audio queue unexpectedly empty.")
            except Exception as e:
                logging.error(f"Error in voice chat loop: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s: %(message)s",
        level=logging.INFO,
    )
    run_voice_chat()

import os
import sys
import json
import wave
import queue
from pathlib import Path
import sounddevice as sd
import soundfile as sf
import logging
from vosk import Model, KaldiRecognizer
from piper.voice import PiperVoice
from gpt4all import GPT4All

# === CONFIGURATION ===
class Config:
    VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "vosk-models/vosk-model-en-us-0.22")
    MODEL_NAME = os.getenv("MODEL_NAME", "Phi-3 Mini Instruct")
    PIPER_MODEL_PATH = os.getenv("PIPER_MODEL_PATH", "piper-voice/en_US-libritts-high.onnx")
    GPT4ALL_MODEL_PATH = os.getenv("GPT4ALL_MODEL_PATH", "gguf-models/Phi-3-mini-4k-instruct-q4.gguf")
    SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are Emma: sarcastic, witty, sometimes dark-humored assistant who secretly flirts with Pedro, Keep responses short: 1-2 sentences max.")
    PIPER_SAMPLE_RATE = int(os.getenv("PIPER_SAMPLE_RATE", 24000))
    VOSK_SAMPLE_RATE = int(os.getenv("VOSK_SAMPLE_RATE", 16000))
    MIN_WORDS = int(os.getenv("MIN_WORDS", 2))
    AUDIO_BLOCKSIZE = int(os.getenv("AUDIO_BLOCKSIZE", 8000))
    AUDIO_DTYPE = os.getenv("AUDIO_DTYPE", "int16")
    AUDIO_CHANNELS = int(os.getenv("AUDIO_CHANNELS", 1))

cfg = Config()

# --- Logging setup ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("emma-chatbot")


class LocalGPT4AllChat:
    def __init__(self, model_path, device=None, system_prompt=None):
        self.model = GPT4All(str(model_path), device=device)
        self.system_prompt = system_prompt or cfg.SYSTEM_PROMPT
        self.chat_history = [{"role": "system", "content": self.system_prompt}]

    def ask(self, user_message, max_tokens=100):
        self.chat_history.append({"role": "user", "content": user_message})
        reply = self.model.generate(
            user_message, max_tokens=max_tokens, streaming=False
        )
        reply_text = reply if isinstance(reply, str) else "".join(reply)
        self.chat_history.append({"role": "assistant", "content": reply_text})
        return reply_text


def load_piper_voice(path):
    """Load and return a Piper voice model."""
    logger.info(f"Loading Piper voice model from {path}")
    try:
        return PiperVoice.load(str(path))
    except Exception as e:
        logger.error(f"Error loading Piper model: {e}")
        sys.exit(1)


def load_vosk_model(path, samplerate):
    """Load and return the Vosk speech recognition model & recognizer."""
    logger.info(f"Loading Vosk model from {path}")
    try:
        model = Model(str(path))
        recognizer = KaldiRecognizer(model, samplerate)
        return recognizer
    except Exception as e:
        logger.error(f"Error loading Vosk model: {e}")
        sys.exit(1)


def load_gpt4all_model():
    logger.info(f"Loading GPT4All model: {cfg.GPT4ALL_MODEL_PATH}")
    model_path = Path(cfg.GPT4ALL_MODEL_PATH).resolve()
    if not model_path.exists():
        logger.critical(
            f"ERROR: GPT4All model file not found at {model_path}\n"
            "Download a .gguf model from https://gpt4all.io/models/ and update the path (env GPT4ALL_MODEL_PATH or config)."
        )
        sys.exit(1)
    try:
        gpt4all_chat = LocalGPT4AllChat(
            model_path, system_prompt=cfg.SYSTEM_PROMPT
        )
        logger.info(f"Model loaded: {model_path}")
        logger.info(f"System prompt: '{cfg.SYSTEM_PROMPT}'")
        return gpt4all_chat
    except Exception as e:
        logger.error(f"Error loading gguf model: {e}")
        sys.exit(1)


def speak(text, voice, filename="test.wav"):
    """Generate a .wav file from text and play it."""
    tmp_path = Path(filename)
    with wave.open(str(tmp_path), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)
    data, samplerate = sf.read(str(tmp_path))
    sd.play(data, samplerate)
    sd.wait()
    try:
        tmp_path.unlink()  # Remove temp file after playback
    except Exception as e:
        logger.warning(f"Could not delete temp file {tmp_path}: {e}")


def audio_callback(indata, frames, time, status, audio_queue):
    """Put recorded audio data into a queue for processing."""
    if status:
        logger.warning(status)
    audio_queue.put(bytes(indata))


def run_voice_chat():
    """Main loop for voice chat system."""
    audio_queue = queue.Queue()
    voice = load_piper_voice(cfg.PIPER_MODEL_PATH)
    recognizer = load_vosk_model(cfg.VOSK_MODEL_PATH, cfg.VOSK_SAMPLE_RATE)
    gpt4all_chat = load_gpt4all_model()

    logger.info("🎤 Start chatting... (Ctrl+C to stop)")
    speak("Hello Pedro", voice)

    try:
        with sd.RawInputStream(
            samplerate=cfg.VOSK_SAMPLE_RATE,
            blocksize=cfg.AUDIO_BLOCKSIZE,
            dtype=cfg.AUDIO_DTYPE,
            channels=cfg.AUDIO_CHANNELS,
            callback=lambda indata, frames, time, status: audio_callback(
                indata, frames, time, status, audio_queue
            ),
        ):
            while True:
                try:
                    data = audio_queue.get()
                    if recognizer.AcceptWaveform(data):
                        recognizer.SetWords(True)
                        recognizer.SetPartialWords(True)
                        res = json.loads(recognizer.Result())
                        user_text = res.get("text", "").strip()
                        word_count = len(user_text.split())

                        if user_text and word_count >= cfg.MIN_WORDS:
                            logger.info(f"You said: {user_text}")
                            logger.info("💬 Generating response from LLM ...")
                            reply = gpt4all_chat.ask(user_text, max_tokens=100)
                            if reply:
                                logger.info(f"Emma says: {reply}")
                                speak(reply, voice)
                                logger.info("💬 You can speak now!")
                        else:
                            # Ignore noise/short phrases
                            pass
                except KeyboardInterrupt:
                    logger.info("\nExiting…")
                    break
    except Exception as e:
        logger.critical(f"Fatal error or audio stream failure: {e}")

if __name__ == "__main__":
    run_voice_chat()

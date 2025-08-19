import sounddevice as sd
import soundfile as sf
import queue
import sys
import json
import requests
import wave
from vosk import Model, KaldiRecognizer
from piper.voice import PiperVoice

# === CONFIGURATION ===
VOSK_MODEL_PATH = "vosk-models/vosk-model-en-us-0.22"
MODEL_NAME = "Phi-3 Mini Instruct"
PIPER_MODEL_PATH = "piper-voice/en_US-libritts-high.onnx"
CHAT_API_URL = "http://localhost:4891/v1/chat/completions"
PIPER_SAMPLE_RATE = 24000
VOSK_SAMPLE_RATE = 16000
MIN_WORDS = 2  # Only trigger when at least 2 words detected

AUDIO_BLOCKSIZE = 8000
AUDIO_DTYPE = "int16"
AUDIO_CHANNELS = 1

def load_piper_voice(path):
    """Load and return a Piper voice model."""
    print("Loading Piper voice model...")
    try:
        return PiperVoice.load(path)
    except Exception as e:
        print(f"Error loading Piper model: {e}")
        sys.exit(1)

def load_vosk_model(path, samplerate):
    """Load and return the Vosk speech recognition model & recognizer."""
    print("Loading Vosk model...")
    try:
        model = Model(path)
        recognizer = KaldiRecognizer(model, samplerate)
        
        return recognizer
    except Exception as e:
        print(f"Error loading Vosk model: {e}")
        sys.exit(1)

def speak(text, voice, filename="test.wav"):
    """Generate a .wav file from text and play it."""
    with wave.open(filename, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)
    data, samplerate = sf.read(filename)
    sd.play(data, samplerate)
    sd.wait()

def ask_chat_api(user_text):
    """Send user text to chat API and return reply or error."""
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": user_text}],
        "max_tokens": 100,
        "temperature": 0.3,
    }
    try:
        r = requests.post(CHAT_API_URL, json=payload)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"].strip()
        else:
            print(f"API Error {r.status_code}: {r.text}", file=sys.stderr)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Failed to reach API: {e}", file=sys.stderr)
        return None

def audio_callback(indata, frames, time, status, audio_queue):
    """Put recorded audio data into a queue for processing."""
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))


def run_voice_chat():
    """Main loop for voice chat system."""
    audio_queue = queue.Queue()
    voice = load_piper_voice(PIPER_MODEL_PATH)
    recognizer = load_vosk_model(VOSK_MODEL_PATH, VOSK_SAMPLE_RATE)

    print("🎤 Start chatting... (Ctrl+C to stop)")
    speak("Hello Pedro", voice)
    
    with sd.RawInputStream(
        samplerate=VOSK_SAMPLE_RATE,
        blocksize=AUDIO_BLOCKSIZE,
        dtype=AUDIO_DTYPE,
        channels=AUDIO_CHANNELS,
        callback=lambda indata, frames, time, status: audio_callback(
            indata, frames, time, status, audio_queue)
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

                    if user_text and word_count >= MIN_WORDS:
                        print(f"You said: {user_text}")
                        print("💬 Generating response from LLM ..")
                        reply = ask_chat_api(user_text)
                        if reply:
                            print(f"Emma says: {reply}")
                            speak(reply, voice)
                            print("💬 You can speak now!")
                    else:
                        # Ignore noise/short phrases
                        pass
            except KeyboardInterrupt:
                print("\nExiting…")
                break

if __name__ == "__main__":
    run_voice_chat()

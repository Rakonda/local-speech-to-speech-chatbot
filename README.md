# Speech to speech chatbot

This project is a voice-based chatbot that uses Vosk for speech recognition, Piper for text-to-speech, and a local Large Language Model (LLM) via CLI (using the Python gpt4all package) for generating responses.

- The chatbot persona is named **Emma** (modifiable).
- The default user name is **Pedro** (modifiable).
- These roles and other settings are easily changed in `chatbot.py` or the LLM context prompt.
- The script has been tested on **Windows** (other OSes may require adjustments).

## How It Works

1. **You speak as Pedro** (default, can be customized) into your microphone.
2. Audio is captured and transcribed to English text using the **Vosk en_US** model.
3. The recognized text is sent to the on-CPU LLM (using the local `gpt4all` Python package running a GGUF model). **No API calls are made.**
4. Emma (the AI) generates a response using the specified LLM model and replies aloud with a natural voice.
5. **Piper TTS** voices Emma's reply using the **en_US female voice** (current voice: `en_US-libritts-high.onnx` + corresponding .json metadata). You can switch voices by updating paths/URLs in `chatbot.py` and `setup_models.py`.

### Chatbot Modes
There are two supported scripts/modes:
- **chatbot.py** — Non-streaming mode: waits for full LLM response before vocalizing.
- **chatbot-stream.py** — Streaming mode: generates and speaks responses incrementally as they're produced by the LLM, for a more natural, responsive feel.

### Model Information (LLM)
- Uses a **GGUF** format model:  
  `gguf-models/Phi-3-mini-4k-instruct-q4.gguf`
- This model must be downloaded (see below) and made available at the specified location before starting the chatbot.

### Performance & Lag Notice
Since all AI generation runs **on your CPU**, expect some lag (hundreds of milliseconds to multiple seconds) both after you finish speaking (while converting speech to text) and while waiting for Emma's response. The delay depends on your CPU speed and the complexity of your question.

### Customization

- **Change Persona or Greetings**: Edit the greeting text, prompt, or role names in `chatbot.py`.
- **Use a Different LLM/Model:**
    - Change `MODEL_NAME` in `chatbot.py` to match any installed model.
    - Ensure you have downloaded and installed the correct GGUF model. Update path in your script or via environment variables as needed.
    - For alternate GGUF models, update the file in `gguf-models/`.
- **Change Vosk or Piper Models:**
    - Download/replace the models (see `setup_models.py` for URLs and local paths).
    - For non-English or alternate voices, update these paths and ensure the files match your target language or persona.
- **Troubleshooting Tips:**
    - If the chatbot does not speak, check your audio input/output devices and model files.
    - If you get errors about missing GGUF models, check the paths and model download.
    - To test alternate configurations, update the RELEVANT parameters in `chatbot.py` and re-run the bot.

## Quick Start (Recommended)

Set up everything with one automated script:

```bash
python setup_env.py
```

This will:
1. Create a new Python virtual environment in `.venv` (if one doesn't exist)
2. Install dependencies from `requirements.txt`
3. Download all required speech and voice models via `setup_models.py`

Then activate the environment:

- **On Windows:**
  ```bash
  .venv\Scripts\activate
  ```
- **On macOS/Linux:**
  ```bash
  source .venv/bin/activate
  ```

Now you can run the chatbot!

```bash
# Non-streamed LLM (full response, more delay)
python chatbot.py

# Streamed LLM (Emma speaks while thinking)
python chatbot-stream.py
```

- Speak into your microphone. The bot will transcribe your text, generate a reply using the GGUF-based LLM, and speak the response as "Emma."
- Press `Ctrl+C` to stop.

## Requirements
- **Python 3.8+**
- **Working microphone & speakers**
- **No API server or backend needed.** Local CPU-only inference.

## Notes
- Model files for Vosk and Piper, gguf will be auto-downloaded into `vosk-models/` and `piper-voice/` and `gguf-models/` folders.
- If you wish to use different voice/language models, update the paths/URLs in `setup_models.py` and `chatbot.py`.
- You may need to adapt device settings or paths for other operating systems or hardware.

---

### Manual Setup (Advanced/Optional)
If you prefer to do steps manually, see previous README versions or break down what `setup_env.py` automates:
1. Create and activate `.venv`
2. `pip install -r requirements.txt`
3. `python setup_models.py`
4. Activate environment and run chatbot.

---

Enjoy your private, local offline AI assistant!

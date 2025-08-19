# Local AI Chatbot

This project is a voice-based chatbot that uses Vosk for speech recognition, Piper for text-to-speech, and a local Large Language Model (LLM) API (tested with GPT4All) for generating responses.

- The chatbot persona is named **Emma** (modifiable).
- The default user name is **Pedro** (modifiable).
- These roles and other settings are easily changed in `chatbot.py` or the LLM context prompt.
- The script has been tested on **Windows** (other OSes may require adjustments).

## How It Works

1. **You speak as Pedro** (default, can be customized) into your microphone.
2. Audio is captured and transcribed to English text using the **Vosk en_US** model.
3. The recognized text is sent to a local LLM server via an API. By default, this expects GPT4All running and the **"Phi-3 Mini Instruct"** model to be available (you must add this model from GPT4All's Add Model panel). If the model is missing, you will receive a 500 API error.
4. Emma (the AI) generates a response using the specified LLM model, and replies aloud with a natural voice.
5. **Piper TTS** voices Emma's reply using the **en_US female voice** (current voice: `en_US-libritts-high.onnx` + corresponding .json metadata). You can switch voices by updating paths/URLs in `chatbot.py` and `setup_models.py`.

### Customization

- **Change Persona or Greetings**: Edit the greeting text, prompt, or role names in `chatbot.py`.
- **Use a Different LLM/Model:**
    - Change `MODEL_NAME` in `chatbot.py` to match any installed model in your GPT4All server.
    - Ensure you have downloaded and installed the correct model in the GPT4All UI panel.
    - If using a different API or backend, adjust the endpoint and/or payload as needed.
- **Change Vosk or Piper Models:**
    - Download/replace the models (see `setup_models.py` for URLs and local paths).
    - For non-English or alternate voices, update these paths and ensure the files match your target language or persona.
- **Troubleshooting Tips:**
    - If the chatbot does not speak, check your audio input/output devices and model files.
    - If the LLM backend returns a 500 error, verify the model name against what your GPT4All server supports and confirm it is downloaded and running.
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
python chatbot.py
```

- Speak into your microphone. The bot will transcribe your text, generate a reply using a running LLM server (e.g., GPT4All), and speak the response as "Emma."
- Press `Ctrl+C` to stop.

## Requirements
- **Python 3.8+**
- **Working microphone & speakers**
- **LLM Backend:**
  - Ensure you have a GPT4All server running at `http://localhost:4891/v1/chat/completions`. See [GPT4All documentation](https://github.com/nomic-ai/gpt4all) for setup details.

## Notes
- Model files for Vosk and Piper will be auto-downloaded into `vosk-models/` and `piper-voice/` folders.
- If you wish to use different voice/language models, update the paths/URLs in `setup_models.py` and `chatbot.py`.
- You may need to adapt device settings or paths for other operating systems or hardware.

---

### Manual Setup (Advanced/Optional)
If you prefer to do steps manually, see previous README versions or break down what `setup_env.py` automates:
1. Create and activate `.venv`
2. `pip install -r requirements.txt`
3. `python setup_models.py`
4. Activate environment and run chatbot.

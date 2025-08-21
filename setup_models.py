import os
import urllib.request
import zipfile
import tempfile
from pathlib import Path

# === Paths and URLs ===
VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"
VOSK_MODEL_DIR = Path("vosk-models/vosk-model-en-us-0.22")
PIPER_MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts/high/en_US-libritts-high.onnx?download=true"
PIPER_MODEL_METADATA_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/libritts/high/en_US-libritts-high.onnx.json?download=true"
PIPER_MODEL_PATH = Path("piper-voice/en_US-libritts-high.onnx")
PIPER_MODEL_METADATA_PATH = Path("piper-voice/en_US-libritts-high.onnx.json")
GGUF_URL = "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf"


def download_file(url, destination):
    import sys
    def progress_bar(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(int(downloaded * 100 / total_size), 100) if total_size > 0 else 0
        bar = ('#' * (percent // 2)).ljust(50)
        sys.stdout.write(f'\r[{bar}] {percent}%')
        sys.stdout.flush()
    print(f"Downloading: {url}")
    urllib.request.urlretrieve(url, destination, reporthook=progress_bar)
    sys.stdout.write('\n')
    print(f"Downloaded to {destination}")


def ensure_vosk_model():
    if VOSK_MODEL_DIR.exists():
        print(f"Vosk model already present at {VOSK_MODEL_DIR}")
        return
    VOSK_MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
    print("Vosk model not found. Downloading...")
    tmp_dir = tempfile.gettempdir()
    vosk_archive_path = os.path.join(tmp_dir, "vosk-model-en-us-0.22.zip")
    download_file(VOSK_MODEL_URL, vosk_archive_path)
    print("Extracting Vosk model zip...")
    with zipfile.ZipFile(vosk_archive_path, 'r') as zip_ref:
        zip_ref.extractall(VOSK_MODEL_DIR.parent)
    print(f"Extracted to {VOSK_MODEL_DIR.parent}")
    try:
        os.remove(vosk_archive_path)
        print(f"Removed temporary archive {vosk_archive_path}")
    except Exception as e:
        print(f"Could not remove temp archive: {e}")


def ensure_piper_model():
    if PIPER_MODEL_PATH.exists():
        print(f"Piper model already present at {PIPER_MODEL_PATH}")
        return
    if PIPER_MODEL_PATH.parent and not PIPER_MODEL_PATH.parent.exists():
        PIPER_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("Piper .onnx model not found. Downloading...")
    download_file(PIPER_MODEL_URL, PIPER_MODEL_PATH)

def ensure_piper_model_metadata():
    if PIPER_MODEL_METADATA_PATH.exists():
        print(f"Piper model metadata already present at {PIPER_MODEL_METADATA_PATH}")
        return
    if PIPER_MODEL_METADATA_PATH.parent and not PIPER_MODEL_METADATA_PATH.parent.exists():
        PIPER_MODEL_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("Piper .onnx metadata not found. Downloading...")
    download_file(PIPER_MODEL_METADATA_URL, PIPER_MODEL_METADATA_PATH)

def ensure_gguf_model():
    """
    Ensures GGUF Phi-3-mini-4k-instruct-q4.gguf is present in gguf-models/.
    Downloads from HuggingFace if not found.
    """
    import sys
    GGUF_DIR = Path("gguf-models")
    GGUF_PATH = GGUF_DIR / "Phi-3-mini-4k-instruct-q4.gguf"
    if GGUF_PATH.exists():
        print(f"GGUF model already present at {GGUF_PATH}")
        return
    GGUF_DIR.mkdir(parents=True, exist_ok=True)
    print("GGUF model not found. Downloading...")
    def progress_bar(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(int(downloaded * 100 / total_size), 100) if total_size > 0 else 0
        bar = ('#' * (percent // 2)).ljust(50)
        sys.stdout.write(f'\r[{bar}] {percent}%')
        sys.stdout.flush()
    import urllib.request
    urllib.request.urlretrieve(GGUF_URL, str(GGUF_PATH), reporthook=progress_bar)
    sys.stdout.write('\n')
    print(f"Downloaded to {GGUF_PATH}")

def main():
    ensure_vosk_model()
    ensure_piper_model()
    ensure_piper_model_metadata()
    ensure_gguf_model()
    print("Model setup complete.")


if __name__ == "__main__":
    main()

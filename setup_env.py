import os
import subprocess
import sys
from pathlib import Path

VENV_DIR = Path('.venv')
REQUIREMENTS = 'requirements.txt'
SETUP_MODELS = 'setup_models.py'

# OS-specific venv script locations
VENV_PYTHON = VENV_DIR / 'Scripts' / 'python.exe' if os.name == 'nt' else VENV_DIR / 'bin' / 'python'


def create_venv():
    print('Creating virtual environment...')
    subprocess.check_call([sys.executable, '-m', 'venv', str(VENV_DIR)])
    print('Virtual environment created at', VENV_DIR)


def install_requirements():
    print('Installing requirements...')
    cmd = [str(VENV_PYTHON), '-m', 'pip', 'install', '-r', REQUIREMENTS]
    subprocess.check_call(cmd)
    print('All dependencies installed.')


def run_setup_models():
    print('Running model setup...')
    cmd = [str(VENV_PYTHON), SETUP_MODELS]
    subprocess.check_call(cmd)
    print('Model resources setup complete.')


def main():
    # 1. Create venv if needed
    if not VENV_DIR.exists():
        create_venv()
    else:
        print('Virtual environment already exists at', VENV_DIR)
    # 2. Install requirements
    install_requirements()
    # 3. Download Vosk/Piper models
    run_setup_models()
    print('Project setup complete. Activate the environment and run chatbot.py.')


if __name__ == '__main__':
    main()

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def ensure_pygame_installed() -> None:
    try:
        import pygame
        return
    except ImportError:
        print("pygame not found. Installing pygame (this requires internet access)...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")]
        )


def main() -> None:
    ensure_pygame_installed()
    subprocess.check_call([sys.executable, str(ROOT / "main.py")])


if __name__ == "__main__":
    main()

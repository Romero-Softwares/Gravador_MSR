import os
import sys
import tempfile
from pathlib import Path


def resource_path(relative_path):
    """Retorna o caminho absoluto do recurso em dev e no PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_default_output_dir():
    videos_dir = Path.home() / "Videos"
    if videos_dir.exists():
        return str(videos_dir)

    return str(Path.home() / "Documents")


def get_temp_paths():
    temp_dir = tempfile.gettempdir()
    return {
        "video": os.path.join(temp_dir, "temp_video.avi"),
        "audio": os.path.join(temp_dir, "temp_audio.wav"),
    }


FFMPEG_PATH = r"C:\ffmpeg\ffmpeg.exe"
DEFAULT_AUDIO_RATE = 44100
DEFAULT_TARGET_FPS = 12.0

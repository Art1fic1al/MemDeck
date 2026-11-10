import numpy
import soundfile
import sounddevice
import audio
from pathlib import Path

FOLDER = Path(__file__).parent / "fx"

FILES = {
    "button_play":   "button-1.wav",
    "button_stop":   "button-2.wav",
    "button_wind":   "button-3.wav",
    "insert":        "casette-insert.mp3",
    "close":         "casette-close.mp3",
    "eject":         "casette-eject.mp3",
    "motor":         "casette-rewind-motor.mp3",
}

clips = {}
rate = None


def load(target_rate):
    global rate
    rate = target_rate
    clips.clear()
    for name, filename in FILES.items():
        path = FOLDER / filename
        try:
            data, file_rate = soundfile.read(path)
            if data.ndim == 1:
                data = data[:, None]
            clips[name] = audio.resample(data, file_rate, target_rate)
        except Exception as error:
            print(f"Could not load sound {filename}: {error}")


def play(name):
    if name not in clips or rate is None:
        return
    try:
        sounddevice.play(clips[name], rate, device=audio.DEVICE)
    except Exception as error:
        print(f"Could not play sound {name}: {error}")

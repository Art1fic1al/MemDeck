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


def resample(data, old_rate, new_rate):
    """Stretch or squash a clip so it plays at the right speed on a new rate."""
    if old_rate == new_rate:
        return data
    new_length = int(len(data) * new_rate / old_rate)
    old_points = numpy.arange(len(data))
    new_points = numpy.linspace(0, len(data) - 1, new_length)
    out = numpy.zeros((new_length, data.shape[1]))
    for channel in range(data.shape[1]):
        out[:, channel] = numpy.interp(new_points, old_points, data[:, channel])
    return out


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
            clips[name] = resample(data, file_rate, target_rate)
        except Exception as error:
            print(f"Could not load sound {filename}: {error}")


def play(name):
    if name not in clips or rate is None:
        return
    try:
        sounddevice.play(clips[name], rate, device=audio.DEVICE)
    except Exception as error:
        print(f"Could not play sound {name}: {error}")

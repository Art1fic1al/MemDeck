import numpy as np
from scipy.signal import butter, sosfilt

# Every knob on the deck, in one place.
#
# apply_chain only ever hands an effect two arguments, the audio and the
# rate, so an effect's own parameter defaults could never be changed from
# outside. Reading the values out of this dict instead means a settings
# panel can write into SETTINGS and the next tape loaded will use them.
SETTINGS = {
    "wow_depth": 0.008,       # slow drift, as a fraction of normal speed
    "wow_rate": 0.9,          # drifts per second
    "flutter_depth": 0.0012,  # fast shimmer, same units
    "flutter_rate": 9.0,
    "drive": 1.2,             # how hard the tape is pushed into saturation
    "hiss": 0.003,            # noise floor
    "cutoff": 12000,          # where the top end starts falling away, in Hz
    "gain": 0.7,              # final output level
}

# A frozen copy taken at import, so there is always a way back.
# dict(SETTINGS) copies it. SETTINGS itself would be the same dict under a
# second name, and editing one would edit both.
DEFAULTS = dict(SETTINGS)


def reset():
    """Put every value back to the factory setting."""
    SETTINGS.clear()
    SETTINGS.update(DEFAULTS)


def wow_flutter(data, samplerate):
    """A tape motor that cannot hold a steady speed.

    wow is the slow drift, flutter is the fast wobble. Depths are fractions
    of normal speed: 0.008 means the tape runs up to 0.8 percent fast and
    0.8 percent slow. Rates are in wobbles per second.
    """
    wow_depth = SETTINGS["wow_depth"]
    flutter_depth = SETTINGS["flutter_depth"]
    if wow_depth <= 0 and flutter_depth <= 0:
        return data

    length = len(data)
    seconds = np.arange(length) / samplerate

    # how fast the tape is moving at each moment
    speed = (1.0
             + wow_depth * np.sin(2 * np.pi * SETTINGS["wow_rate"] * seconds)
             + flutter_depth * np.sin(2 * np.pi * SETTINGS["flutter_rate"] * seconds))

    # adding up the speeds gives the position the head has reached
    read_at = np.cumsum(speed)
    read_at -= read_at[0]
    read_at = np.clip(read_at, 0, length - 1)

    # those positions land between samples, so read the value in between
    source = np.arange(length)
    out = np.zeros_like(data)
    for channel in range(data.shape[1]):
        out[:, channel] = np.interp(read_at, source, data[:, channel])
    return out


def saturate(data, samplerate):
    drive = SETTINGS["drive"]
    if drive <= 0:
        return data
    return np.tanh(data * drive) / np.tanh(drive)


def hiss(data, samplerate):
    amount = SETTINGS["hiss"]
    if amount <= 0:
        return data
    return data + np.random.normal(0, amount, data.shape)


def rolloff(data, samplerate):
    cutoff = SETTINGS["cutoff"]
    # A filter cannot be set above half the sample rate, and a cutoff that
    # high is not removing anything audible anyway, so treat it as off.
    if cutoff <= 0 or cutoff >= samplerate / 2:
        return data
    sos = butter(4, cutoff, btype="low", output="sos", fs=samplerate)
    return sosfilt(sos, data, axis=0)


def gain(data, samplerate):
    return data * SETTINGS["gain"]


def apply_chain(data, samplerate, chain):
    for effect in chain:
        data = effect(data, samplerate)
    return data


CHAIN = [wow_flutter, saturate, hiss, rolloff, gain]

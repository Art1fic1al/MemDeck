import numpy as np
from scipy.signal import butter, sosfilt

def saturate(data, samplerate, drive=1.2):
    return np.tanh(data * drive) / np.tanh(drive)

def hiss(data, samplerate, amount=0.003):
    return data + np.random.normal(0, amount, data.shape)

def gain(data, samplerate, amount=0.7):
    return data * amount

def apply_chain(data, samplerate, chain):
    for effect in chain:
        data = effect(data, samplerate)
    return data

def rolloff(data, samplerate, cutoff=12000):
    sos = butter(4, cutoff, btype='low', output='sos', fs=samplerate,)
    out = sosfilt(sos, data, axis=0)
    return out

def wow_flutter(data, samplerate,
                wow_depth=0.008, wow_rate=0.9,
                flutter_depth=0.0012, flutter_rate=9.0):
    """A tape motor that cannot hold a steady speed.

    wow is the slow drift, flutter is the fast wobble. Depths are fractions
    of normal speed: 0.004 means the tape runs up to 0.4 percent fast and
    0.4 percent slow. Rates are in wobbles per second.
    """
    length = len(data)
    seconds = np.arange(length) / samplerate

    # how fast the tape is moving at each moment
    speed = (1.0
             + wow_depth * np.sin(2 * np.pi * wow_rate * seconds)
             + flutter_depth * np.sin(2 * np.pi * flutter_rate * seconds))

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

CHAIN = [wow_flutter, saturate, hiss, rolloff, gain]

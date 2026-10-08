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

def rolloff(data, samplerate, cutoff=8000):
    sos = butter(4, cutoff, btype='low', output='sos', fs=samplerate,)
    out = sosfilt(sos, data, axis=0)
    return out

CHAIN = [saturate, hiss, rolloff, gain]
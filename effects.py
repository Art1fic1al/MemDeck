import numpy as np

def saturate(data, drive=1.2):
    return np.tanh(data * drive) / np.tanh(drive)
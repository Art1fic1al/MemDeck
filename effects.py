import numpy as np

def saturate(data, drive=1.2):
    return np.tanh(data * drive) / np.tanh(drive)

def hiss(data, amount=0.003):
    return data + np.random.normal(0, amount, data.shape)

def apply_chain(data, chain):
    for effect in chain:
        data = effect(data)
    return data

CHAIN = [saturate, hiss]
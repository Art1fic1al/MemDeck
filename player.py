import soundfile
import sounddevice
import effects

def play(path):
    data, samplerate = soundfile.read(path)
    data = effects.apply_chain(data, samplerate, effects.CHAIN)
    position = 0

    def callback(outdata, frames, time, status):
        nonlocal position
        chunk = data[position:position + frames]
        if len(chunk) == 0:
            raise sounddevice.CallbackStop
        outdata[:len(chunk)] = chunk
        outdata[len(chunk):] = 0
        position += len(chunk)

    with sounddevice.OutputStream(
        samplerate=samplerate,
        channels=data.shape[1],
        callback=callback,
    ):
        print("Press Enter to stop playback")
        input()
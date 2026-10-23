import soundfile
import sounddevice
import effects

class Player:
    def __init__(self, path):
        self.data, self.samplerate = soundfile.read(path)
        self.data = effects.apply_chain(self.data, self.samplerate, effects.CHAIN)
        self.position = 0

    def callback(self, outdata, frames, time, status):
        chunk = self.data[self.position:self.position + frames]
        if len(chunk) == 0:
            raise sounddevice.CallbackStop
        outdata[:len(chunk)] = chunk
        outdata[len(chunk):] = 0
        self.position += len(chunk)

    def play(self):
        with sounddevice.OutputStream(
            samplerate=self.samplerate,
            channels=self.data.shape[1],
            callback=self.callback,
        ):
            print("Press Enter to stop playback")
            input()
import soundfile
import sounddevice
import effects

class Player:
    def __init__(self, path):
        self.data, self.samplerate = soundfile.read(path)
        self.data = effects.apply_chain(self.data, self.samplerate, effects.CHAIN)
        self.position = 0
        self.paused = False

    def callback(self, outdata, frames, time, status):
        if self.paused:
            outdata.fill(0)
            return
        
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
            print("Press Enter to stop playback, P to pause, R to resume.")
            while True:
                key = input("\n\n").lower()
                if key == "p":
                    self.paused = True
                elif key == "r":
                    self.paused = False
                elif key == "":
                    break
                else:
                    print("\n\nInvalid input. Press Enter to stop playback, P to pause, R to resume.")
import soundfile
import sounddevice
import effects
import sfx
import audio

class Player:
    def __init__(self, path):
        self.data, self.samplerate = soundfile.read(path)
        self.data = effects.apply_chain(self.data, self.samplerate, effects.CHAIN)
        self.position = 0
        self.speed = 1
        self.target_speed = 1
        self.ramp = 0
        self.paused = False

    def set_speed(self, value):
        # Ask the motor to change speed. Winding releases the stop."""
        self.target_speed = value
        self.paused = False

    def step_speed(self, frames):
        # Move one notch toward the target speed, slowly, like a real motor."""
        if self.speed == self.target_speed:
            self.ramp = 0
            return
        self.ramp += frames
        if self.ramp < self.samplerate // 3:
            return
        self.ramp = 0
        if self.target_speed > self.speed:
            self.speed += 1
        else:
            self.speed -= 1
        if self.speed == 0:
            # a slice step of zero is not allowed, so skip straight past it
            self.speed = 1 if self.target_speed > 0 else -1

    def callback(self, outdata, frames, time, status):
        if self.paused:
            outdata.fill(0)
            return

        self.step_speed(frames)

        stop = self.position + frames * self.speed
        if stop < 0:
            stop = None

        chunk = self.data[self.position:stop:self.speed]
        if len(chunk) == 0:
            raise sounddevice.CallbackStop
        outdata[:len(chunk)] = chunk
        outdata[len(chunk):] = 0

        self.position += frames * self.speed
        if self.position < 0:
            self.position = 0
            self.set_speed(1)

    def play(self):
        controls = "Press Enter to EJECT tape, P to PLAY, S to STOP, D to FAST FORWARD, A to REVERSE."
        with sounddevice.OutputStream(
            samplerate=self.samplerate,
            channels=self.data.shape[1],
            callback=self.callback,
            device=audio.DEVICE,
        ):
            print(controls)
            while True:
                key = input("\n\n").lower()
                if key == "s":
                    sfx.play("button_stop")
                    self.paused = True
                elif key == "p":
                    sfx.play("button_play")
                    self.set_speed(1)
                elif key == "d":
                    sfx.play("button_wind")
                    self.set_speed(4)
                elif key == "a":
                    sfx.play("button_wind")
                    self.set_speed(-4)
                elif key == "":
                    sfx.play("eject")
                    break
                else:
                    print("\n\nInvalid input. " + controls)

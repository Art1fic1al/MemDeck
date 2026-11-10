import numpy
import soundfile
import sounddevice
import effects
import sfx
import audio

class Player:
    def __init__(self, path):
        data, file_rate = soundfile.read(path)
        if data.ndim == 1:
            # a mono file arrives flat. Give it a second column so the rest
            # of the code can keep treating it as rows of channels.
            data = numpy.column_stack([data, data])

        if audio.RATE is not None and file_rate != audio.RATE:
            print(f"Tape runs at {file_rate} Hz, deck runs at {audio.RATE} Hz. Converting.")
            data = audio.resample(data, file_rate, audio.RATE)
            file_rate = audio.RATE

        self.samplerate = file_rate
        self.data = effects.apply_chain(data, self.samplerate, effects.CHAIN)
        self.position = 0
        self.speed = 1
        self.target_speed = 1
        self.ramp = 0
        self.paused = False
        self.stream = None

    # ----- the tape mechanism -----

    def set_speed(self, value):
        # Ask the motor to change speed. Winding releases the stop.
        self.target_speed = value
        self.paused = False

    def step_speed(self, frames):
        # Move one notch toward the target speed, slowly, like a real motor.
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
            # Reached one end of the tape. The motor stops, but the tape stays
            # in the deck, so rewind and play still work without re-inserting.
            outdata.fill(0)
            self.position = min(max(self.position, 0), len(self.data))
            return
        outdata[:len(chunk)] = chunk
        outdata[len(chunk):] = 0

        self.position += frames * self.speed
        if self.position < 0:
            self.position = 0
            self.set_speed(1)

    # ----- the stream, opened and closed on demand -----

    def open(self):
        # Start the sound card calling our callback.
        if self.stream is not None:
            return
        self.stream = sounddevice.OutputStream(
            samplerate=self.samplerate,
            channels=self.data.shape[1],
            callback=self.callback,
            device=audio.DEVICE,
        )
        self.stream.start()

    def close(self):
        # Stop it, and let go of the device.
        if self.stream is None:
            return
        self.stream.stop()
        self.stream.close()
        self.stream = None

    def is_running(self):
        return self.stream is not None

    # ----- the buttons on the front of the deck -----
    # Anything can press these: a keyboard loop, a GUI button, a test.

    def press_play(self):
        sfx.play("button_play")
        self.set_speed(1)

    def press_stop(self):
        sfx.play("button_stop")
        self.paused = True

    def press_forward(self):
        sfx.play("button_wind")
        self.set_speed(4)

    def press_rewind(self):
        sfx.play("button_wind")
        self.set_speed(-4)

    def press_eject(self):
        sfx.play("eject")
        self.close()

    # ----- one way of driving the deck: the keyboard -----

    def console(self):
        controls = "Press Enter to EJECT tape, P to PLAY, S to STOP, D to FAST FORWARD, A to REVERSE."
        self.open()
        print(controls)
        while self.is_running():
            key = input("\n\n").lower()
            if key == "s":
                self.press_stop()
            elif key == "p":
                self.press_play()
            elif key == "d":
                self.press_forward()
            elif key == "a":
                self.press_rewind()
            elif key == "":
                self.press_eject()
            else:
                print("\n\nInvalid input. " + controls)

import numpy
import soundfile
import sounddevice
import effects
import sfx
import audio

# How the motor behaves. Both are speed gained or lost per second, so the
# time to reach a speed follows from how far away it is: at MOTOR 3.0 the
# deck takes a third of a second to reach play and 1.3 seconds to reach a
# wind. These two numbers are the dials for the whole feel of the transport.
MOTOR = 3.0       # the motor pulling the tape up to speed
BRAKE = 6.0       # the brake pulling it back down, twice as hard
WIND_SPEED = 4.0  # how fast fast forward and rewind run


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
        self.channels = self.data.shape[1]
        self.length = len(self.data)

        # Position is now a fraction of a sample, not a whole one, so the
        # head can sit between two samples.
        self.position = 0.0
        self.speed = 0.0
        self.target_speed = 1.0   # inserting a tape starts the motor
        self.stream = None

    # ----- the tape mechanism -----

    def set_speed(self, value):
        # Ask the motor for a speed. It gets there over the next fraction
        # of a second, it does not jump.
        self.target_speed = float(value)

    def stop_motor(self):
        # Cut the motor dead. Used by autostop at either end of the tape.
        self.speed = 0.0
        self.target_speed = 0.0

    def step_speed(self, frames):
        # Move the speed one buffer's worth closer to what was asked for.
        if self.speed == self.target_speed:
            return

        gap = self.target_speed - self.speed

        # Slowing down is braking, speeding up is the motor. They are not
        # the same strength, which is why a reversal sounds lopsided: it
        # brakes hard to a stop, then climbs away slowly the other way.
        braking = (self.speed > 0 and gap < 0) or (self.speed < 0 and gap > 0)
        seconds = frames / self.samplerate
        step = (BRAKE if braking else MOTOR) * seconds

        if abs(gap) <= step:
            self.speed = self.target_speed
        elif gap > 0:
            self.speed += step
        else:
            self.speed -= step

    def read(self, frames):
        """Pull `frames` samples off the tape at the current speed.

        The positions we want land between real samples, so each one is
        mixed from the two samples either side of it. That mixing is the
        whole reason speed is allowed to be a fraction.
        """
        wanted = self.position + numpy.arange(frames) * self.speed

        # Keep only the part still on the tape. The positions only ever
        # climb or only ever fall, so counting the good ones also tells us
        # where the good ones stop.
        if self.speed > 0:
            usable = int(numpy.count_nonzero(wanted <= self.length - 1))
        else:
            usable = int(numpy.count_nonzero(wanted >= 0))

        if usable == 0:
            return numpy.zeros((0, self.channels))

        wanted = wanted[:usable]

        left = wanted.astype(numpy.int64)               # the sample before
        right = numpy.minimum(left + 1, self.length - 1)  # the sample after
        blend = (wanted - left)[:, None]                # how far between them

        return self.data[left] * (1.0 - blend) + self.data[right] * blend

    def callback(self, outdata, frames, time, status):
        self.step_speed(frames)

        if self.speed == 0.0:
            # Standing still. Nothing to read, nothing to play.
            outdata.fill(0)
            return

        # Pressed against an end and still being pushed into it.
        if (self.speed > 0 and self.position >= self.length - 1) or \
           (self.speed < 0 and self.position <= 0):
            outdata.fill(0)
            self.stop_motor()
            return

        chunk = self.read(frames)
        outdata[:len(chunk)] = chunk
        outdata[len(chunk):] = 0

        self.position += frames * self.speed

        # Autostop. The motor cuts but the tape stays in the deck, so the
        # other direction still works without re-inserting.
        if self.position >= self.length - 1:
            self.position = float(self.length - 1)
            self.stop_motor()
        elif self.position <= 0:
            self.position = 0.0
            self.stop_motor()

    # ----- what the deck looks like from outside -----

    def progress(self):
        # How far through the tape we are, 0.0 to 1.0.
        if self.length < 2:
            return 0.0
        return min(max(self.position / (self.length - 1), 0.0), 1.0)

    def seconds(self):
        return self.position / self.samplerate

    def duration(self):
        return self.length / self.samplerate

    def at_end(self):
        return self.position >= self.length - 1

    def at_start(self):
        return self.position <= 0

    def state(self):
        if self.speed == 0.0:
            return "stopped"
        if self.speed < 0:
            return "rewind"
        if self.speed > 1.5:
            return "forward"
        return "play"

    # ----- the stream, opened and closed on demand -----

    def open(self):
        # Start the sound card calling our callback.
        if self.stream is not None:
            return
        self.stream = sounddevice.OutputStream(
            samplerate=self.samplerate,
            channels=self.channels,
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
        self.set_speed(1.0)

    def press_stop(self):
        sfx.play("button_stop")
        self.set_speed(0.0)

    def press_forward(self):
        sfx.play("button_wind")
        self.set_speed(WIND_SPEED)

    def press_rewind(self):
        sfx.play("button_wind")
        self.set_speed(-WIND_SPEED)

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

"""Checks the transport and the reel geometry.

Run it from the project folder:

    python tests.py

player.py normally needs a sound card. Here soundfile and sounddevice are
replaced with stand-ins, so these checks run anywhere, with no audio device
and no music files.
"""
import sys
import types
import math
import numpy

HOLDER = {}

sf = types.ModuleType("soundfile")
sf.read = lambda path: (HOLDER["data"], 44100)
sys.modules["soundfile"] = sf

sd = types.ModuleType("sounddevice")


class OutputStream:
    def __init__(self, **kw):
        self.kw = kw

    def start(self):
        pass

    def stop(self):
        pass

    def close(self):
        pass


sd.OutputStream = OutputStream
sd.play = lambda *a, **k: None
sd.query_devices = lambda *a, **k: []
sd.query_hostapis = lambda *a, **k: {"name": "stub"}
sys.modules["sounddevice"] = sd

import effects
import player as player_module
import reels

effects.CHAIN = []   # test the transport, not the colouring

FAILURES = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")
    if not ok:
        FAILURES.append(name)


def ramp(length=1000):
    column = numpy.arange(length, dtype=float)
    return numpy.column_stack([column, column])


def make(length=1000):
    HOLDER["data"] = ramp(length)
    return player_module.Player("stub.wav")


# ----- reading at whole and fractional speeds -----

p = make()
p.position, p.speed = 0.0, 1.0
chunk = p.read(10)
check("speed 1.0 reproduces the samples exactly",
      numpy.allclose(chunk[:, 0], numpy.arange(10)))

p.position, p.speed = 0.0, 0.5
chunk = p.read(4)
check("speed 0.5 reads halfway between samples",
      numpy.allclose(chunk[:, 0], [0.0, 0.5, 1.0, 1.5]),
      str(chunk[:, 0]))

p.position, p.speed = 0.0, 1.25
chunk = p.read(4)
check("speed 1.25 steps by a quarter sample",
      numpy.allclose(chunk[:, 0], [0.0, 1.25, 2.5, 3.75]),
      str(chunk[:, 0]))

p.position, p.speed = 10.0, -1.0
chunk = p.read(5)
check("negative speed walks backwards",
      numpy.allclose(chunk[:, 0], [10, 9, 8, 7, 6]),
      str(chunk[:, 0]))

p.position, p.speed = 2.0, -1.0
chunk = p.read(10)
check("running off the front truncates instead of wrapping",
      len(chunk) == 3 and numpy.allclose(chunk[:, 0], [2, 1, 0]),
      f"len={len(chunk)}")

p.position, p.speed = 995.0, 1.0
chunk = p.read(10)
check("running off the end truncates",
      len(chunk) == 5 and numpy.allclose(chunk[:, 0], [995, 996, 997, 998, 999]),
      f"len={len(chunk)}")

p.position, p.speed = 0.0, 4.0
chunk = p.read(8)
check("wind speed 4.0 still lands on real samples",
      numpy.allclose(chunk[:, 0], numpy.arange(8) * 4.0))

# interpolation on something that is not a straight line
HOLDER["data"] = numpy.column_stack([
    numpy.sin(numpy.arange(2000) * 0.01),
    numpy.sin(numpy.arange(2000) * 0.01)])
q = player_module.Player("stub.wav")
q.position, q.speed = 100.0, 1.0
chunk = q.read(64)
check("a sine read at speed 1.0 is bit exact",
      numpy.allclose(chunk[:, 0], numpy.sin((numpy.arange(64) + 100) * 0.01)))

q.position, q.speed = 100.0, 0.5
chunk = q.read(64)
truth = numpy.sin((100 + numpy.arange(64) * 0.5) * 0.01)
check("a sine read at speed 0.5 is close to the true curve",
      numpy.max(numpy.abs(chunk[:, 0] - truth)) < 1e-4,
      f"worst error {numpy.max(numpy.abs(chunk[:, 0] - truth)):.2e}")

# ----- the motor -----

p = make()
p.speed, p.target_speed = 0.0, 1.0
ticks = 0
while p.speed != p.target_speed and ticks < 10000:
    p.step_speed(512)
    ticks += 1
spin_up_seconds = ticks * 512 / 44100
check("0 to play speed takes 1/MOTOR seconds",
      abs(spin_up_seconds - 1.0 / player_module.MOTOR) < 0.02,
      f"{spin_up_seconds:.3f}s")

p.target_speed = 0.0
ticks = 0
while p.speed != p.target_speed and ticks < 10000:
    p.step_speed(512)
    ticks += 1
brake_seconds = ticks * 512 / 44100
check("play speed to a standstill takes 1/BRAKE seconds",
      abs(brake_seconds - 1.0 / player_module.BRAKE) < 0.02,
      f"{brake_seconds:.3f}s")

p.speed, p.target_speed = 4.0, -4.0
seen_zero = False
ticks = 0
while p.speed != p.target_speed and ticks < 100000:
    p.step_speed(512)
    if abs(p.speed) < 0.2:
        seen_zero = True
    ticks += 1
check("a reversal passes through a standstill", seen_zero)
check("a reversal reaches the other direction", abs(p.speed + 4.0) < 1e-9,
      f"ended at {p.speed}")

p.speed, p.target_speed = 0.0, 0.0
p.step_speed(512)
check("speed 0.0 is allowed to sit still", p.speed == 0.0)

# ----- a whole tape, played through the callback -----

p = make(44100 * 3)          # three seconds
frames = 512
out = numpy.zeros((frames, 2))
calls = 0
ever_played = False
while calls < 2000:
    p.callback(out, frames, None, None)
    if p.state() != "stopped":
        ever_played = True
    if ever_played and p.state() == "stopped":
        break
    calls += 1

check("play reaches the end of the tape and stops",
      p.at_end() and p.state() == "stopped",
      f"progress {p.progress():.4f} after {calls} buffers")
check("the end takes about the length of the tape plus spin up",
      3.0 < calls * frames / 44100 < 4.0,
      f"{calls * frames / 44100:.2f}s of buffers for a 3.00s tape")

p.press_rewind()
calls = 0
while calls < 4000 and not p.at_start():
    p.callback(out, frames, None, None)
    calls += 1
check("rewind from the end reaches the start", p.at_start(),
      f"progress {p.progress():.4f}")
check("the motor stops itself at the start", p.state() == "stopped")
check("progress stays inside 0.0 and 1.0", 0.0 <= p.progress() <= 1.0)

p.press_play()
p.callback(out, frames, None, None)
check("play works again after a full rewind, no re-insert",
      p.target_speed == 1.0 and not p.at_start())

p.press_stop()
calls = 0
while calls < 100 and p.state() != "stopped":
    p.callback(out, frames, None, None)
    calls += 1
check("stop brings the motor to a standstill", p.state() == "stopped")
before = p.position
p.callback(out, frames, None, None)
check("a stopped tape does not creep", p.position == before)
check("a stopped tape is silent", numpy.allclose(out, 0.0))

long_tape = make(44100 * 30)     # thirty seconds, long enough to wind on
long_tape.press_forward()
calls = 0
while calls < 4000 and long_tape.speed != long_tape.target_speed:
    long_tape.callback(out, frames, None, None)
    calls += 1
check("fast forward reaches full wind speed",
      long_tape.state() == "forward"
      and abs(long_tape.speed - player_module.WIND_SPEED) < 1e-9,
      f"speed {long_tape.speed:.2f} after {calls * frames / 44100:.2f}s")

# ----- the geometry -----

check("an empty reel is the bare hub", abs(reels.radius(0.0) - reels.HUB) < 1e-9)
check("a full reel is the full radius", abs(reels.radius(1.0) - reels.FULL) < 1e-9)
check("half the tape is NOT half the radius",
      abs(reels.radius(0.5) - 17.71) < 0.01,
      f"{reels.radius(0.5):.2f} mm")

area_half = reels.radius(0.5) ** 2 - reels.HUB ** 2
area_full = reels.FULL ** 2 - reels.HUB ** 2
check("half the tape is half the wound area",
      abs(area_half / area_full - 0.5) < 1e-9)

for played in (0.0, 0.25, 0.5, 0.75, 1.0):
    supply = reels.radius(1.0 - played)
    takeup = reels.radius(played)
    left, right = reels.span(supply, takeup)

    # the line through the two points, as a unit direction and a normal
    dx, dy = right[0] - left[0], right[1] - left[1]
    size = math.hypot(dx, dy)
    nx, ny = -dy / size, dx / size

    # distance from each hub centre to that line
    d_supply = abs(nx * (-reels.CENTRE - left[0]) + ny * (0 - left[1]))
    d_takeup = abs(nx * (reels.CENTRE - left[0]) + ny * (0 - left[1]))

    on_supply = math.hypot(left[0] + reels.CENTRE, left[1])
    on_takeup = math.hypot(right[0] - reels.CENTRE, right[1])

    ok = (abs(d_supply - supply) < 1e-9 and abs(d_takeup - takeup) < 1e-9
          and abs(on_supply - supply) < 1e-9 and abs(on_takeup - takeup) < 1e-9)
    check(f"the span at {played * 100:.0f}% rests on both packs", ok,
          f"gap {d_supply - supply:+.2e} / {d_takeup - takeup:+.2e}")

check("a full pack turns slower than an empty one",
      reels.rpm(reels.FULL) < reels.rpm(reels.HUB),
      f"{reels.rpm(reels.FULL):.1f} rpm full, {reels.rpm(reels.HUB):.1f} rpm empty")

turns_full = reels.turn(reels.TAPE_SPEED, reels.FULL) / (2 * math.pi)
check("a full pack turns about 0.34 times a second",
      abs(turns_full - 0.337) < 0.01, f"{turns_full:.3f} rev/s")

check("wow starts at 1.0", abs(reels.wow_scale(0.0) - 1.0) < 1e-9)
check("wow roughly doubles by the end of the tape",
      1.9 < reels.wow_scale(1.0) < 2.1, f"{reels.wow_scale(1.0):.2f}")

# total tape length implied by the geometry, as a sanity check against a real C60
seconds_per_side = 1800
metres = reels.TAPE_SPEED * seconds_per_side / 1000.0
check("the real tape speed gives a plausible C60 length",
      80 < metres < 95, f"{metres:.1f} m for a 30 minute side")

print()
if FAILURES:
    print(f"{len(FAILURES)} FAILED: {FAILURES}")
    raise SystemExit(1)
print("all checks passed")

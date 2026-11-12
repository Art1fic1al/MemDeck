"""The geometry of two reels in a cassette shell.

Pure maths. No drawing, no tkinter, no audio. Everything here is in
millimetres and radians, taken from a real Compact Cassette, so the
numbers mean something outside this program.

Nothing here knows how fast the audio is playing, and that is deliberate.
A real deck pulls tape past the head with a capstan at a fixed speed. The
reels turn at whatever rate that forces on them. Reel size is a result of
playback, never a cause of it.
"""

import math

HUB = 11.0        # radius of the bare plastic hub
FULL = 22.5       # radius of a reel wound full
CENTRE = 21.0     # how far each hub sits from the middle of the shell
TAPE_SPEED = 47.625   # millimetres of tape per second, the cassette standard


def radius(fill):
    """Radius of a reel that is `fill` full, 0.0 empty to 1.0 full.

    Tape is a ribbon of fixed thickness wound in a spiral, so the amount of
    tape on a reel is its cross-section AREA, not its radius. Area goes with
    the square of the radius, so the radius follows a square root.

    Half the tape does not mean half the radius. It means a radius of about
    17.7, two thirds of the way out, because the outer turns are longer and
    hold more tape each.
    """
    fill = min(max(fill, 0.0), 1.0)
    return math.sqrt(HUB * HUB + fill * (FULL * FULL - HUB * HUB))


def span(supply, takeup):
    """Where the straight run of tape leaves one pack and meets the other.

    Returns two points in millimetres, measured from the middle of the two
    hubs, positive y toward the front of the shell.

    This is the external tangent: the one straight line that rests on both
    packs from the same side without cutting between them. It is found by
    looking for the line's normal rather than the line itself. A unit
    normal n and an offset k describe the line n . p = k, and the condition
    "this line is exactly `supply` away from one hub and `takeup` away from
    the other, both on the same side" fixes n in one step.
    """
    across = 2.0 * CENTRE
    nx = (takeup - supply) / across
    nx = min(max(nx, -1.0), 1.0)
    ny = -math.sqrt(max(0.0, 1.0 - nx * nx))

    left = (-CENTRE - supply * nx, -supply * ny)
    right = (CENTRE - takeup * nx, -takeup * ny)
    return left, right


def turn(distance, pack):
    """Radians a pack of radius `pack` turns when `distance` of tape passes.

    Same unit for both. This is the whole reason the two reels visibly turn
    at different rates: the same tape passes over both, but the small one
    has less circumference to spend it on, so it has to turn further.
    """
    if pack <= 0:
        return 0.0
    return distance / pack


def rpm(pack):
    """Revolutions per minute of a pack of this radius during normal play."""
    if pack <= 0:
        return 0.0
    return TAPE_SPEED * 60.0 / (2.0 * math.pi * pack)


def wow_scale(played):
    """How much worse the speed wobble gets as the supply reel empties.

    A full supply reel is heavy and steadies the transport. A nearly empty
    one has almost no inertia, so every motor imperfection shows. 1.0 at the
    start of the tape, about 2.0 at the end.
    """
    return FULL / radius(1.0 - played)


def report():
    """Print the geometry across a tape. Diagnostics, run it directly."""
    print(f"{'played':>7} {'supply':>8} {'takeup':>8} "
          f"{'leaves at':>16} {'arrives at':>16} {'supply rpm':>11} {'wow':>6}")
    for step in range(0, 11):
        played = step / 10.0
        supply = radius(1.0 - played)
        takeup = radius(played)
        left, right = span(supply, takeup)
        print(f"{played * 100:>6.0f}% {supply:>8.1f} {takeup:>8.1f} "
              f"({left[0]:>6.1f},{left[1]:>6.1f}) "
              f"({right[0]:>6.1f},{right[1]:>6.1f}) "
              f"{rpm(supply):>11.1f} {wow_scale(played):>6.2f}")


if __name__ == "__main__":
    report()

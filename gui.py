"""The window. A second way of driving the deck, beside player.console().

It owns no transport logic of its own. Every button calls the same
press_ method the keyboard loop calls, and everything it draws it reads
back out of the player and out of reels.py.
"""

import math
import time
import tkinter

import audio
import library
import reels
import sfx
from player import Player

WIDTH = 520
HEIGHT = 360
SCALE = 4.0          # pixels per millimetre of real cassette
FPS = 30

BODY = "#1d1f21"     # the deck's shell
PANEL = "#111315"    # the window you look through
EDGE = "#2c3033"
ACCENT = "#4dbeff"
TEXT = "#d7dadc"
DIM = "#6a7075"
TAPE = "#3a2a1d"
TAPE_EDGE = "#56402d"

MONO = ("Consolas", 10)
SMALL = ("Consolas", 8)

# The tape window, and the middle of the two hubs inside it.
WINDOW = (30, 48, 490, 248)
CX = (WINDOW[0] + WINDOW[2]) / 2
CY = (WINDOW[1] + WINDOW[3]) / 2


def clock(seconds):
    seconds = int(max(seconds, 0))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class Deck:
    def __init__(self):
        self.root = tkinter.Tk()
        self.root.title("MemDeck")
        self.root.overrideredirect(True)      # no title bar, no border
        self.root.resizable(False, False)
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.configure(bg=BODY)

        self.canvas = tkinter.Canvas(self.root, width=WIDTH, height=HEIGHT,
                                     bg=BODY, highlightthickness=0)
        self.canvas.pack()

        self.tracks = library.load()
        self.picked = 0
        self.player = None

        # Where each pack has turned to. Carried between frames, because
        # rotation is something that accumulates, not something you can
        # work out from the position alone.
        self.supply_angle = 0.0
        self.takeup_angle = 0.0
        self.last_frame = time.perf_counter()

        self.grab = None
        self.alive = True

        self.build()
        self.bind_keys()
        self.root.after(1000 // FPS, self.tick)

    # ----- building the face of the deck -----

    def build(self):
        self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT,
                                     fill=BODY, outline=EDGE, width=1)
        # Dragging is bound to the canvas as a whole, so the deck can be
        # picked up anywhere, and refused when the press landed on a button.
        self.canvas.bind("<Button-1>", self.press_shell)
        self.canvas.bind("<B1-Motion>", self.drag_shell)

        self.canvas.create_text(16, 15, text="MEMDECK: Privet Hannka", fill=ACCENT,
                                font=("Consolas", 11, "bold"), anchor="w")

        self.chip("dir", 372, 6, 36, 18, "DIR", self.do_folder)
        self.chip("prev", 414, 6, 26, 18, "<", self.do_prev)
        self.chip("next", 446, 6, 26, 18, ">", self.do_next)
        self.chip("quit", 482, 6, 26, 18, "X", self.do_quit)

        self.canvas.create_rectangle(*WINDOW, fill=PANEL, outline=EDGE, width=1)

        # The head block and capstan, where the tape is actually read.
        self.canvas.create_rectangle(CX - 26, WINDOW[3] - 26, CX + 26, WINDOW[3] - 6,
                                     fill=EDGE, outline="")
        self.canvas.create_text(CX, WINDOW[3] - 16, text="HEAD", fill=DIM, font=SMALL)

        self.name_text = self.canvas.create_text(
            36, 273, text="", fill=TEXT, font=MONO, anchor="w")
        self.clock_text = self.canvas.create_text(
            484, 273, text="", fill=DIM, font=MONO, anchor="e")

        self.buttons = []
        left = 24
        for tag, label, action, lit in (
            ("rew", "REW", self.do_rewind, "rewind"),
            ("play", "PLAY", self.do_play, "play"),
            ("stop", "STOP", self.do_stop, "stopped"),
            ("ffwd", "FFWD", self.do_forward, "forward"),
            ("eject", "EJECT", self.do_eject, None),
        ):
            rect = self.chip(tag, left, 300, 88, 40, label, action)
            self.buttons.append({"rect": rect, "lit": lit})
            left += 96

    def chip(self, tag, x, y, w, h, label, action):
        """One clickable block: a rectangle and its label, sharing a tag."""
        rect = self.canvas.create_rectangle(x, y, x + w, y + h,
                                            fill=EDGE, outline=EDGE,
                                            tags=(tag, "chip"))
        self.canvas.create_text(x + w / 2, y + h / 2, text=label, fill=TEXT,
                                font=MONO, tags=(tag, "chip"))
        self.canvas.tag_bind(tag, "<Button-1>", lambda event: action())
        return rect

    def bind_keys(self):
        self.root.bind("<p>", lambda event: self.do_play())
        self.root.bind("<s>", lambda event: self.do_stop())
        self.root.bind("<d>", lambda event: self.do_forward())
        self.root.bind("<a>", lambda event: self.do_rewind())
        self.root.bind("<e>", lambda event: self.do_eject())
        self.root.bind("<Left>", lambda event: self.do_prev())
        self.root.bind("<Right>", lambda event: self.do_next())

    # ----- moving the window -----

    def press_shell(self, event):
        # "current" is whatever the mouse is over. A press on a button is
        # that button's business, so the window does not pick it up.
        under = self.canvas.find_withtag("current")
        if under and "chip" in self.canvas.gettags(under[0]):
            self.grab = None
            return
        self.grab = (event.x, event.y)

    def drag_shell(self, event):
        if self.grab is None:
            return
        x = self.root.winfo_x() + event.x - self.grab[0]
        y = self.root.winfo_y() + event.y - self.grab[1]
        self.root.geometry(f"+{x}+{y}")

    # ----- the buttons -----

    def do_play(self):
        if self.player is None:
            self.insert()
            return
        self.player.press_play()

    def do_stop(self):
        if self.player:
            self.player.press_stop()

    def do_forward(self):
        if self.player:
            self.player.press_forward()

    def do_rewind(self):
        if self.player:
            self.player.press_rewind()

    def do_eject(self):
        if self.player is None:
            return
        self.player.press_eject()
        self.player = None
        self.supply_angle = 0.0
        self.takeup_angle = 0.0

    def do_prev(self):
        if self.tracks:
            self.picked = (self.picked - 1) % len(self.tracks)

    def do_next(self):
        if self.tracks:
            self.picked = (self.picked + 1) % len(self.tracks)

    def do_folder(self):
        folder = library.pick_folder(parent=self.root)
        if folder is None:
            return
        if library.scan_folder(folder):
            self.tracks = library.load()
            self.picked = min(self.picked, max(len(self.tracks) - 1, 0))

    def do_quit(self):
        # alive stops the next tick. Without it the already scheduled frame
        # fires against a destroyed window and raises.
        self.alive = False
        if self.player:
            self.player.close()
        self.root.destroy()

    def insert(self):
        if not self.tracks:
            return
        entry = self.tracks[self.picked]

        # Loading runs the whole effects chain, which takes a moment on a
        # long track, and tkinter cannot redraw while it runs. So say so
        # first, and force the redraw before starting.
        self.canvas.itemconfigure(self.name_text, text="LOADING ...")
        self.canvas.update_idletasks()

        sfx.play("close")
        try:
            self.player = Player(entry["path"])
        except Exception as error:
            print(f"Could not load {entry.get('filename')}: {error}")
            self.player = None
            return
        self.player.open()

    # ----- the moving parts -----

    def tick(self):
        if not self.alive:
            return
        now = time.perf_counter()
        elapsed = now - self.last_frame
        self.last_frame = now

        self.draw_reels(elapsed)
        self.draw_readout()
        self.root.after(1000 // FPS, self.tick)

    def draw_reels(self, elapsed):
        self.canvas.delete("spin")

        played = self.player.progress() if self.player else 0.0
        supply = reels.radius(1.0 - played)
        takeup = reels.radius(played)

        if self.player and self.player.state() != "stopped":
            # How much tape went past the head since the last frame. Both
            # packs turn the same way; the small one simply has to turn
            # further to swallow the same length of tape.
            moved = reels.TAPE_SPEED * elapsed * self.player.speed
            self.supply_angle += reels.turn(moved, supply)
            self.takeup_angle += reels.turn(moved, takeup)

        left, right = reels.span(supply, takeup)
        self.canvas.create_line(CX + left[0] * SCALE, CY + left[1] * SCALE,
                                CX + right[0] * SCALE, CY + right[1] * SCALE,
                                fill=TAPE_EDGE, width=2, tags="spin")

        self.pack(-reels.CENTRE, supply, self.supply_angle)
        self.pack(reels.CENTRE, takeup, self.takeup_angle)

    def pack(self, offset, size, angle):
        """One wound pack: the tape on it, the hub, and the spokes."""
        x = CX + offset * SCALE
        radius = size * SCALE
        hub = reels.HUB * SCALE

        self.canvas.create_oval(x - radius, CY - radius, x + radius, CY + radius,
                                fill=TAPE, outline=TAPE_EDGE, tags="spin")

        # A mark on the outside edge, so the pack itself is visibly turning
        # and not just the hub inside it.
        self.canvas.create_line(
            x + math.cos(angle) * radius * 0.82,
            CY + math.sin(angle) * radius * 0.82,
            x + math.cos(angle) * radius,
            CY + math.sin(angle) * radius,
            fill=TAPE_EDGE, width=2, tags="spin")

        self.canvas.create_oval(x - hub, CY - hub, x + hub, CY + hub,
                                fill=PANEL, outline=EDGE, tags="spin")
        for spoke in range(3):
            turned = angle + spoke * 2.0 * math.pi / 3.0
            self.canvas.create_line(
                x + math.cos(turned) * hub * 0.3,
                CY + math.sin(turned) * hub * 0.3,
                x + math.cos(turned) * hub * 0.92,
                CY + math.sin(turned) * hub * 0.92,
                fill=DIM, width=2, tags="spin")

    def draw_readout(self):
        if not self.tracks:
            self.canvas.itemconfigure(self.name_text,
                                      text="No tapes. Press DIR to add a folder.")
            self.canvas.itemconfigure(self.clock_text, text="--:-- / --:--")
        else:
            entry = self.tracks[self.picked]
            mark = "[IN] " if self.player else f"[{self.picked + 1}/{len(self.tracks)}] "
            self.canvas.itemconfigure(self.name_text,
                                      text=mark + str(entry.get("filename", "?"))[:46])
            if self.player:
                self.canvas.itemconfigure(
                    self.clock_text,
                    text=f"{clock(self.player.seconds())} / {clock(self.player.duration())}")
            else:
                self.canvas.itemconfigure(
                    self.clock_text,
                    text="--:-- / " + clock(entry.get("seconds", 0) or 0))

        state = self.player.state() if self.player else "stopped"
        for button in self.buttons:
            on = button["lit"] is not None and button["lit"] == state
            self.canvas.itemconfigure(button["rect"],
                                      outline=ACCENT if on else EDGE)

    def run(self):
        # A window with no title bar is not given the keyboard by the window
        # manager, so take it, or none of the key bindings would ever fire.
        self.root.focus_force()
        self.root.mainloop()


def main():
    audio.report()
    if audio.setup() is None:
        return
    sfx.load(audio.RATE)
    Deck().run()


if __name__ == "__main__":
    main()

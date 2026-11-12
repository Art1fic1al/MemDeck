from pathlib import Path
from prompts import ynr
import library
from player import Player
import sfx
import audio


def add_folder():
    """Add one folder to the catalogue, by picker or by typed path."""
    answer = input("\n[P] Pick a folder | [T] Type a path\n\n").lower()
    if answer == "p":
        folder = library.pick_folder()
        if folder is None:
            print("\nNothing chosen.\n")
            return
    else:
        folder = Path(input("\nEnter desired filepath to search\n\n"))
    library.scan_folder(folder)


def show(tracks):
    for number, entry in enumerate(tracks, start=1):
        print(f"{number:>4}. {entry.get('filename', '?')}")
    print(f"\n{len(tracks)} tapes, {library.total_time(tracks)} in total.\n")


def choose(tracks):
    """Ask for a track number until a real one comes back. None to stop."""
    while True:
        try:
            numtrack = int(input("Please input track number\n\n")) - 1
        except ValueError:
            print("\nInvalid input. Please input a valid track number.\n\n")
            continue

        if numtrack < 0 or numtrack >= len(tracks):
            print("\nInvalid input. Please input a valid track number.\n\n")
            continue

        picked = tracks[numtrack]
        print(f"\n\n{picked['filename']}\n\n")
        answer = input("Play selected track?\n___________________________\n"
                       "[Y] Yes | [N] No | [R] Redo\n\n").lower()
        # ynr exits the program on N, which is what we want here: N means
        # "I am done", R means "let me pick again".
        if ynr(answer):
            return picked


# The catalogue survives between runs now, so a scan is only needed when
# there is nothing saved or when something new should be added.
tracks = library.load()

if tracks:
    show(tracks)
    if input("Add another folder?\n[Y] Yes | [N] No\n\n").lower() == "y":
        add_folder()
        tracks = library.load()
        show(tracks)
else:
    while not tracks:
        print("\nNo catalogue yet.")
        add_folder()
        tracks = library.load()
    show(tracks)


audio.report()
if audio.setup() is None:
    raise SystemExit
sfx.load(audio.RATE)


if input("\n[W] Open the window | [K] Keyboard only\n\n").lower() == "w":
    import gui
    gui.Deck().run()
    raise SystemExit


while True:
    picked = choose(tracks)
    sfx.play("close")
    player = Player(picked["path"])
    player.console()

from pathlib import Path
import  json
from models import Track
from prompts import yn, ynr
from library import scan_folder
from player import Player
import sfx
import audio



while True:
    folder = Path(input("\nEnter desired filepath to search\n\n"))
    answer = str(input(f"\nSearch directory {folder} for files?\n___________________________\n[Y] Yes | [N] No | [R] Redo\n\n")).lower()
    if not ynr(answer):
        continue
    if scan_folder(folder):
        break


with open("casette.json", "r", encoding="utf-8") as f:
    tracks = json.load(f)

    while True:
        answer = input(f"Play tracks?\n_________________\n[Y] Yes | [N] No\n\n").lower()
        if yn(answer):
            break


audio.report()
audio.setup()
sfx.load(audio.RATE)


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
    answer = input(f"Play selected track?\n___________________________\n[Y] Yes | [N] No | [R] Redo\n\n").lower()
    if not ynr(answer):
        continue

    sfx.play("close")

    player = Player(picked["path"])
    player.console()

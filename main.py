from ast import Return
from pathlib import Path
import  json
from models import Track
from prompts import yn, ynr
from library import scan_folder
from player import play

                                                                                                                                             

while True:
    folder = Path(input("\nEnter desired filepath to search\n\n"))
    answer = str(input(f"\nSearch directory {folder} for files?\n___________________________\n[Y] Yes | [N] No | [R] Redo\n\n")).lower()
    if ynr(answer):
        break
 
 
scan_folder(folder)

 
with open("casette.json", "r", encoding="utf-8") as f:
    tracks = json.load(f)

    while True:
        answer = input(f"Play tracks?\n_________________\n[Y] Yes | [N] No\n\n").lower()
        if yn(answer):
            break


while True:
    try:
        numtrack = int(input("Please input track number\n\n")) - 1
        if numtrack >= 0 and numtrack < len(tracks):
            break
        elif numtrack < 0 or numtrack >= len(tracks):
            print("\nInvalid input. Please input a valid track number.\n\n")
            continue
    except ValueError:
        print("\nInvalid input. Please input a valid track number.\n\n")
        continue
picked = tracks[numtrack]
print(f"\n\n{picked['filename']}\n\n")
answer = str(input(f"Play selected track?\n___________________________\n[Y] Yes | [N] No | [R] Redo\n\n")).lower()
if ynr(answer):
    play(picked["path"])
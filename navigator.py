from pathlib import Path
import mutagen
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.mp4 import MP4
import datetime
import  json
import soundfile
import sounddevice
from models import Track
 
def YN(answer):
    if answer == "y":
        print("\nProceeding\n")
        return True
    elif answer == "n":
        print("\nCancelling\n")
        exit()
    elif answer == "r":
        print("\nRedoing Input\n")
        return False
    else:
        print(f"The answer \"{answer}\" is not a valid answer. Please input only the aforementioned characters.")
        return False
 
 
class Track:
    def __init__(self, filename, seconds, path):
        self.filename = filename
        self.seconds = seconds
        self.path = path
 
    def to_dict(self):
        return {"filename": self.filename, "seconds": self.seconds, "path": self.path}
 
 
audionumber = 0
lib_total_seconds = 0
library = []
 
 
while True:
    folder = Path(input("\nEnter desired filepath to search\n\n"))
    answer = str(input(f"\nSearch directory {folder} for files?\n___________________________\n[Y] Yes | [N] No | [R] Redo\n\n")).lower()
    if YN(answer):
        break
 
 
try:

    for file in folder.iterdir():
        if file.suffix.lower() in [".mp3", ".mp4", ".wav"]:
            extension = file.suffix.lower()
            audionumber = audionumber + 1
            try:
                if extension == ".mp3":
                    audio = MP3(file)
                elif extension == ".wav":
                    audio = WAVE(file)
                elif extension == ".mp4":
                    audio = MP4(file)
            except mutagen.MutagenError:
                print(f"{audionumber}. {file.name}:\n[x] INVALID FILE!\n")
                continue
 
            length = round(audio.info.length)
            duration = datetime.timedelta(seconds=length)
            lib_total_seconds = lib_total_seconds + length
 
            songlet = f"{audionumber}. ▶ {file.name}\n[{duration}]"
            print(f"{songlet}\n")
 
            library.append(Track(file.name, length, str(file)))
 
    lib_total_time = datetime.timedelta(seconds=lib_total_seconds)
    print(f"\nTotal library playtime: {lib_total_time}\n")
 
    plain = []
    for track in library:
        plain.append(track.to_dict())

    with open("casette.json", "w", encoding="utf-8") as f:
        json.dump(plain, f, indent=2, ensure_ascii=False)
 
    print(f"Saved {len(plain)} tracks to casette.json\n")
 
except FileNotFoundError:
    print("\nError!\n")
 

with open("casette.json", "r", encoding="utf-8") as f:
    tracks = json.load(f)
    while True:
        answer = input(f"Play tracks?\n\n")
        if YN(answer):
            break
    numtrack = int(input("Please input track number\n\n"))-1
    picked = tracks[numtrack]
    print(f"\n\n{picked["filename"]}\n\n")
    answer = str(input(f"Play selected track?\n___________________________\n[Y] Yes | [N] No | [R] Redo\n\n")).lower()
    if YN(answer):
        data, samplerate = soundfile.read(picked["path"])
        sounddevice.play(data, samplerate)
        sounddevice.wait()
        input()
        exit()
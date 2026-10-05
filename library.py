import  json
import datetime
from models import Track
import mutagen
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.mp4 import MP4

def scan_folder(folder):
    audionumber = 0
    lib_total_seconds = 0
    library = []
    
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
import json
import datetime
from pathlib import Path
from models import Track
import mutagen
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.mp4 import MP4

CATALOGUE = Path("casette.json")
EXTENSIONS = (".mp3", ".wav", ".mp4", ".flac", ".ogg")


def load():
    """Read the saved catalogue. An empty list if there is not one yet."""
    if not CATALOGUE.exists():
        return []
    try:
        with open(CATALOGUE, "r", encoding="utf-8") as f:
            saved = json.load(f)
    except (json.JSONDecodeError, OSError) as error:
        print(f"Could not read {CATALOGUE}: {error}")
        return []
    if not isinstance(saved, list):
        print(f"{CATALOGUE} does not hold a list of tracks. Ignoring it.")
        return []
    return saved


def save(tracks):
    with open(CATALOGUE, "w", encoding="utf-8") as f:
        json.dump(tracks, f, indent=2, ensure_ascii=False)


def read_tags(file):
    """One file to a Track, or None if it cannot be read."""
    extension = file.suffix.lower()
    try:
        if extension == ".mp3":
            tags = MP3(file)
        elif extension == ".wav":
            tags = WAVE(file)
        elif extension == ".mp4":
            tags = MP4(file)
        else:
            tags = mutagen.File(file)
        if tags is None:
            return None
        return Track(file.name, round(tags.info.length), str(file))
    except (mutagen.MutagenError, OSError, AttributeError):
        return None


def total_time(tracks):
    seconds = 0
    for entry in tracks:
        seconds += entry.get("seconds", 0) or 0
    return datetime.timedelta(seconds=seconds)


def scan_folder(folder, merge=True):
    """Walk a folder and its subfolders, adding what it finds to the catalogue.

    Hands back True if the catalogue ended up with something in it.

    merge=True keeps what was already catalogued and adds anything new,
    matched on the full path. merge=False throws the old catalogue away.
    """
    folder = Path(folder)

    if not folder.exists():
        print(f"\nThere is no folder called {folder}.\n")
        return False
    if not folder.is_dir():
        print(f"\n{folder} is a file, not a folder.\n")
        return False

    found = []
    # rglob walks subfolders too. glob would only look at the top level.
    for file in sorted(folder.rglob("*")):
        if not file.is_file() or file.suffix.lower() not in EXTENSIONS:
            continue
        track = read_tags(file)
        if track is None:
            print(f"[x] {file.name}: cannot be read.")
            continue
        entry = track.to_dict()
        found.append(entry)
        stamp = datetime.timedelta(seconds=entry.get("seconds", 0) or 0)
        print(f"{len(found):>4}. {file.name}  [{stamp}]")

    if not found:
        # Nothing playable in there. Leave the old catalogue alone.
        print(f"\nNo audio files found in {folder}.\n")
        return False

    if merge:
        tracks = load()
        known = set()
        for entry in tracks:
            known.add(entry.get("path"))
        added = []
        for entry in found:
            if entry.get("path") not in known:
                added.append(entry)
        tracks.extend(added)
        print(f"\n{len(added)} new, {len(found) - len(added)} already catalogued.")
    else:
        tracks = found

    save(tracks)
    print(f"Catalogue now holds {len(tracks)} tracks, {total_time(tracks)} in total.\n")
    return True


def pick_folder(parent=None):
    """Open the operating system's own folder chooser. None if cancelled.

    parent is an existing tkinter window. Pass one when a window is already
    open: a second Tk() alongside the first makes tkinter misbehave.
    """
    try:
        import tkinter
        from tkinter import filedialog
    except ImportError:
        print("tkinter is not available, so the folder chooser cannot open.")
        return None

    title = "Choose a folder of music"
    if parent is None:
        root = tkinter.Tk()
        root.withdraw()
        chosen = filedialog.askdirectory(title=title)
        root.destroy()
    else:
        chosen = filedialog.askdirectory(title=title, parent=parent)

    if not chosen:
        return None
    return Path(chosen)

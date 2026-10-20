# MemDeck

A cassette-style audio player for a local music library, written in Python.

## The goal

A desktop player that runs a music collection through analogue tape processing on the way to the speakers: saturation, hiss, frequency rolloff, and eventually the pitch wobble of an imperfect motor.

## Status

The library and playback spine is complete, and three of the four tape effects are implemented and audible. Wow and flutter, the GUI and packaging are still ahead.

## What it does now

- Scans a folder for audio files (`.mp3`, `.wav`, `.mp4`)
- Reads duration and metadata with `mutagen`, skipping unreadable or corrupt files rather than crashing
- Reports each track and the total playtime of the library
- Saves the result as a JSON catalogue that survives between runs
- Loads that catalogue back and plays a selected track
- **Processes the audio through a tape effects chain on the way to the speakers**
- Playback can be interrupted at any point
- Plays through a streaming audio callback, which is what makes pause and seek possible later

Tested against a real library of roughly 400 files.

## The effects chain

Audio is decoded to a numpy array and passed through an ordered list of effect functions before playback. Each effect takes an array and the samplerate, and returns an array of the same shape, so effects can be added, removed or reordered by editing one list.

| Effect | What it does |
| --- | --- |
| `saturate` | Soft-clips peaks with a `tanh` curve, compressing loud parts the way tape does instead of clipping them flat. |
| `hiss` | Adds low-level gaussian noise, the noise floor of a magnetic tape. |
| `rolloff` | A fourth-order Butterworth low-pass filter that attenuates high frequencies. This is the most audible part of the tape character. |
| `gain` | Output level, used to compensate for the loudness saturation adds so the effect can be judged honestly. |

## Planned

- Wow and flutter: the slow pitch drift and fast wobble of an imperfect tape motor
- A `Player` object with pause, stop and seek
- User-named cassettes: custom collections with editable titles
- Metadata editing, writing corrected artist and title tags back to the files
- A graphical cassette-deck interface
- Packaging as a standalone executable

## Requirements

Python 3.12 or newer. The code uses nested quotes inside f-strings, which is only valid from 3.12 onward.

```
py -m pip install mutagen soundfile sounddevice scipy
```

## How to run

```
py main.py
```

The program will ask for a folder path to scan, list what it finds, save the catalogue, and then let you pick a track by number and play it.

## Project structure

| File | Responsibility |
| --- | --- |
| `main.py` | Wires everything together. The file you run. |
| `models.py` | The `Track` class: one track's data, and conversion to a plain dict for saving. |
| `library.py` | Scanning a folder and writing the JSON catalogue. |
| `player.py` | Turning a file path into sound. |
| `effects.py` | The tape effects and the chain that applies them. |
| `prompts.py` | Yes/no and yes/no/redo input handling. |

Imports run in one direction only: `main` knows about the other modules, and none of them know about `main`. Anything a module needs from its caller is passed in as an argument.

## Known limitations

- `soundfile` cannot decode AAC, so `.m4a` and `.mp4` files are catalogued correctly but will fail at playback.
- The scanner reads one folder and does not descend into subfolders.
- Track selection does not yet validate its input, so a non-numeric entry will raise an error.
- Effect settings are defaults in the code and cannot be changed without editing `effects.py`.

## Why

I am a musician, which is how I ended up building an audio project rather than a to-do app. MemDeck is also my portfolio piece, developed in my own time alongside the theoretical phase of a Fachinformatiker Anwendungsentwicklung retraining programme.

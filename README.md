# MemDeck

A cassette-style audio player for a local music library, written in Python.

## The goal

A desktop player that runs a music collection through analogue tape processing on the way to the speakers: saturation, hiss, frequency rolloff, and the pitch wobble of an imperfect motor. Not a general-purpose player with a tape skin on it. A deck that behaves like a deck.

## Status

The library, the playback engine and all four tape effects are working. The transport has play, stop, fast forward and rewind, with mechanical button sounds and a motor that takes time to wind up. The GUI and packaging are what remain.

## What it does now

- Scans a folder for audio files (`.mp3`, `.wav`, `.mp4`)
- Reads duration and metadata with `mutagen`, skipping unreadable or corrupt files rather than crashing
- Lists every track with its running time, and the total playtime of the library
- Saves the result as a JSON catalogue that survives between runs
- Loads that catalogue back and plays a selected track
- **Processes the audio through a tape effects chain on the way to the speakers**
- Plays through a streaming audio callback, which is what makes the transport controls possible
- **Transport: play, stop, fast forward and rewind**, with the motor accelerating into speed rather than snapping to it
- Plays mechanical cassette sounds on each button, resampled to match the output device

Tested against a real library of roughly 400 files.

## The effects chain

Audio is decoded to a numpy array and passed through an ordered list of effect functions before playback. Each effect takes an array and the samplerate and returns an array of the same shape, so effects can be added, removed or reordered by editing one list.

| Effect | What it does |
| --- | --- |
| `wow_flutter` | Varies the playback speed slightly and continuously, so the pitch drifts the way a tape does when the motor cannot hold a steady speed. Wow is the slow drift, flutter the fast shimmer. |
| `saturate` | Soft-clips peaks with a `tanh` curve, compressing loud parts the way tape does instead of clipping them flat. |
| `hiss` | Adds low-level gaussian noise, the noise floor of a magnetic tape. |
| `rolloff` | A fourth-order Butterworth low-pass filter that attenuates high frequencies. This is the most audible part of the tape character. |
| `gain` | Output level, used to compensate for the loudness saturation adds so the effect can be judged honestly. |

`wow_flutter` runs first because a transport wobble happens at the head, before the tape's own colouration.

## The transport

Playback runs on a callback that the sound card calls a few hundred times a second. The callback reads a slice of the audio starting at the current position, using the current speed as the slice step. Speed 1 is play, 4 is fast forward, -4 is rewind.

Because the callback reads that speed fresh on every call, changing it takes effect within milliseconds and nothing has to be torn down or restarted. The motor's wind-up is a target speed that the current speed walks toward a notch at a time.

| Key | Does |
| --- | --- |
| `P` | Play |
| `S` | Stop |
| `D` | Fast forward |
| `A` | Rewind |
| Enter | Eject |

## Design decisions

**No numeric seek.** A general-purpose audio player lets you jump to a timestamp. A cassette deck never could. Its controls were play, stop, pause, rewind and fast forward, plus a mechanical counter you could reset to zero. Jumping to 1:30 is not something a tape can do, so MemDeck does not do it either.

What replaces it is cue and review. On decks that had it, the head stayed against the tape while winding, so you heard the audio rush past at high speed and high pitch. In code that is a speed value the playback callback reads on every call, used as the step of the slice it takes, rather than a jump to a new position.

The rule the project follows: if a real deck could not do it, MemDeck does not get it for free just because the audio library makes it easy.

## Requirements

Python 3.12 or newer. The code uses nested quotes inside f-strings, which is only valid from 3.12 onward.

```
py -m pip install mutagen soundfile sounddevice scipy numpy
```

## How to run

```
py main.py
```

The program asks for a folder path to scan, lists what it finds, saves the catalogue, and then lets you pick a track by number and play it.

## Project structure

| File | Responsibility |
| --- | --- |
| `main.py` | Wires everything together. The file you run. |
| `models.py` | The `Track` class: one track's data, and conversion to a plain dict for saving. |
| `library.py` | Scanning a folder and writing the JSON catalogue. |
| `player.py` | The `Player` class: the playback callback and the transport. |
| `effects.py` | The tape effects and the chain that applies them. |
| `sfx.py` | Loads the mechanical cassette sounds and plays them on demand. |
| `audio.py` | Chooses an output device, because this is less automatic than it should be. |
| `prompts.py` | Yes/no and yes/no/redo input handling. |

Imports run in one direction only: `main` knows about the other modules, and none of them know about `main`. Anything a module needs from its caller is passed in as an argument.

## Planned

- A motor whirr that loops while winding and stops when the tape does
- Fractional wind speeds, so the motor accelerates smoothly instead of in whole-number steps
- The insertion sequence: handling the cassette, sliding it in, closing the tray. These are mouse actions, so they belong with the GUI
- User-named cassettes: custom collections with editable titles
- Metadata editing, writing corrected artist and title tags back to the files
- A graphical cassette-deck interface
- Packaging as a standalone executable

## Known limitations

- `soundfile` cannot decode AAC, so `.m4a` and `.mp4` files are catalogued correctly but will fail at playback.
- The scanner reads one folder and does not descend into subfolders.
- Effect settings are defaults in the code and cannot be changed without editing `effects.py`.
- Wind speed steps in whole numbers, so the motor's acceleration is audible as steps rather than a smooth climb. Fixing this needs fractional playback speed, which is the same machinery `wow_flutter` uses.
- Applying the effects chain adds a second or two to the load time of each track.
- On Windows, PortAudio probes kernel-streaming (WDM-KS) devices when `sounddevice` is imported. On a machine with audio devices that are present but disabled, that probe can take the Windows audio service down with it, after which no usable output device exists. `audio.py` detects this case and says so rather than failing obscurely. The underlying fix would be an audio backend that does not touch WDM-KS.

## Why

I am a musician, which is how I ended up building an audio project rather than a to-do app. MemDeck is also my portfolio piece, developed in my own time alongside the theoretical phase of a Fachinformatiker Anwendungsentwicklung retraining programme.

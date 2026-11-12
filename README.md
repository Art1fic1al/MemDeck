# MemDeck

A cassette-style audio player for a local music library, written in Python.

## The goal

A desktop player that runs a music collection through analogue tape processing on the way to the speakers: saturation, hiss, frequency rolloff, and the pitch wobble of an imperfect motor. Not a general-purpose player with a tape skin on it. A deck that behaves like a deck.

## Status

The library, the playback engine and all five tape effects are working. The transport has play, stop, fast forward and rewind, with mechanical button sounds and a motor that accelerates and brakes at its own rate. A borderless window drives that same transport, with both cassette reels drawn according to cassette geometry. The artwork, a settings panel and packaging are what remain of the main roadmap.

## What it does now

- Scans a folder and its subfolders for audio files (`.mp3`, `.wav`, `.mp4`, `.flac`, `.ogg`), either by typed path or through the operating system's own folder picker
- Reads duration and metadata with `mutagen`, skipping unreadable or corrupt files rather than crashing
- Lists every track with its running time, and the total playtime of the library
- Saves the result as a JSON catalogue that survives between runs, and merges new folders into it instead of replacing it
- Processes the audio through a tape effects chain on the way to the speakers
- Plays through a streaming audio callback, which is what makes the transport controls possible
- Transport: play, stop, fast forward and rewind, at any fractional speed, with the motor accelerating and braking at its own rate rather than snapping between them
- Plays mechanical cassette sounds on each button, resampled to match the output device
- A borderless, draggable window with working transport buttons, a counter, and both reels turning at the rates the geometry demands

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

Every value the effects use lives in `effects.SETTINGS`, with the factory values kept in `effects.DEFAULTS` and `effects.reset()` to go back to them. Setting a depth to zero turns that effect off.

## The transport

Playback runs on a callback that the sound card calls a few hundred times a second. The callback reads the audio at the current position and the current speed. Speed 1.0 is play, 4.0 is fast forward, -4.0 is rewind, 0.0 is a tape standing still.

Speed is a fraction, not a whole number, so the positions being read land between real samples. Each one is mixed from the two samples either side of it. That is what lets the motor accelerate continuously rather than in steps, and what makes a speed of zero a legal state rather than an error.

Because the callback reads that speed fresh on every call, changing it takes effect within milliseconds and nothing has to be torn down or restarted. `MOTOR` and `BRAKE` in `player.py` are the acceleration and deceleration rates, and between them they are the entire feel of the transport.

Both ends of the tape autostop: the motor cuts, the tape stays in the deck, and winding the other way works immediately without re-inserting it.

| Key | Does |
| --- | --- |
| `P` | Play |
| `S` | Stop |
| `D` | Fast forward |
| `A` | Rewind |
| `E` or Enter | Eject |

## The reels

`reels.py` is the cassette geometry, in millimetres, taken from a real Compact Cassette: an 11.0 mm hub, a 22.5 mm full reel, hubs 21.0 mm either side of the middle, and tape running at 47.625 mm per second, which is the 1 7/8 inches per second the format is defined at.

Two things in it are worth stating, because both are easy to get wrong:

**A reel's radius follows area, not length.** Tape is a ribbon of fixed thickness wound in a spiral, so the amount on a reel is the area of the ring it forms. Half the tape played is not half the radius. It is 17.7 mm out of 22.5, about two thirds of the way out, because the outer turns are longer as they need to hold more tape per rotation.

**Reel size does not drive playback speed.** A real deck pulls the tape past the head with a capstan at a fixed speed no matter how full the reels are. Reel size is a result of playback, never a cause of it. What it does affect is the wobble: a full supply reel is heavy and steadies the transport, and a nearly empty one has no inertia left, so wow roughly doubles by the end of a tape. That is what `reels.wow_scale` is designed around.

The straight run of tape between the two packs is the external tangent of two circles, solved for the direction the line faces rather than for the line itself.

`reels.py` imports `math` and nothing else. Run it directly for the full table.

## Design decisions

**No numeric seek.** A general-purpose audio player lets you jump to a timestamp. A cassette deck never could. Its controls were play, stop, pause, rewind and fast forward, plus a mechanical counter you could reset to zero. Jumping to 1:30 is not something a tape can do, so MemDeck does not do it either.

What replaces it is cue and review. On decks that had it, the head stayed against the tape while winding, so you heard the audio rush past at high speed and high pitch. In code that is a speed value the playback callback reads on every call, rather than a jump to a new position.

The rule the project follows: if a real deck could not do it, MemDeck does not get it for free just because the audio library makes it easy.

## Requirements

Python 3.12 or newer.

```
py -m pip install mutagen soundfile sounddevice scipy numpy
```

## How to run

```
py main.py
```

loads the saved catalogue, offers to add a folder, and then asks whether to open the window or stay on the keyboard.

```
py gui.py
```

opens the window directly.

```
py tests.py
```

runs the checks on the transport and the reel geometry. They use stand-ins for the audio library, so they need no sound card and no music files.

## Project structure

| File | Responsibility |
| --- | --- |
| `main.py` | Wires everything together. The file you run. |
| `models.py` | The `Track` class: one track's data, and conversion to a plain dict for saving. |
| `library.py` | Scanning folders, and the JSON catalogue. |
| `player.py` | The `Player` class: the playback callback and the transport. |
| `effects.py` | The tape effects, the chain that applies them, and their settings. |
| `reels.py` | Cassette reel geometry. Pure maths, no drawing and no audio. |
| `gui.py` | The window. A second way of driving the same transport. |
| `sfx.py` | Loads the mechanical cassette sounds and plays them on demand. |
| `audio.py` | Chooses an output device, because this is less automatic than it should be. |
| `prompts.py` | Yes/no and yes/no/redo input handling. |
| `tests.py` | Checks on the transport and the geometry. |

Imports run in one direction only: `main` knows about the other modules, and none of them know about `main`. Anything a module needs from its caller is passed in as an argument. `gui.py` owns no transport logic of its own; its buttons call the same methods the keyboard loop calls.

## Planned

- Artwork for the deck face, replacing the drawn rectangles
- Wow driven by `reels.wow_scale`, which needs the effects chain to run live rather than once at load
- A motor whirr that loops while winding and stops when the tape does
- Loading on a second thread, so the window stops freezing while a track is processed
- A settings panel writing into `effects.SETTINGS`
- The insertion sequence: handling the cassette, sliding it in, closing the tray
- User-named cassettes: custom collections with editable titles
- Metadata editing, writing corrected artist and title tags back to the files
- Packaging as a standalone executable

## Known limitations

- `soundfile` cannot decode AAC, so `.m4a` and `.mp4` files are catalogued correctly but will fail at playback.
- Effect settings take effect on the next tape loaded, not the one currently in the deck, because the chain runs once at load.
- Applying the effects chain adds a second or two to the load time of each track, and the window does not redraw while it runs.
- Sound effects get a stream each, and `sounddevice.play` replaces whatever is already playing, so two of them cut each other off. This is what blocks the motor whirr.
- Every cassette is drawn as a full one regardless of track length. That is correct for a shop-bought tape and arguably wrong for a deck whose tapes hold one track each.
- On Windows, PortAudio probes kernel-streaming (WDM-KS) devices when `sounddevice` is imported. On a machine with audio devices that are present but disabled, that probe can take the Windows audio service down with it, after which no usable output device exists. `audio.py` detects this case and says so rather than failing obscurely. The underlying fix would be an audio backend that does not touch WDM-KS.

## How this was built

MemDeck is my design; the behaviour, the constraints, and the decisions about what the virtual deck is and is not allowed to do are mine, and the reasoning for them is in this file.

A significant portion of later implementations was written with AI assistance, specifically via incremental prompting with Claude Opus 5. I originally felt critical of the use of AI-authored code in this project, however time-constraints and an interest in understanding the future of this work expanded the scope of tooling involved.

However, if you want to know whether I understand my own project, then ask me about any part of it live, and I'll happily guide you through; module for module or character for character.

## Why

I am a musician, which is how I ended up building an audio project rather than a to-do app. MemDeck is also my portfolio piece, developed in my own time alongside the theoretical phase of a Fachinformatiker Anwendungsentwicklung retraining programme.

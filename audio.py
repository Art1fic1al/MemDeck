import sounddevice

# Notes on this machine, learned the hard way:
#
# PortAudio enumerates every Windows audio API when sounddevice is imported.
# One of them, WDM-KS, is kernel streaming: it bypasses the Windows audio
# service and pokes drivers directly. Some USB headsets react badly to being
# probed that way, which can take the audio service down with them.
#
# The other three APIs all go through the audio service. So if only WDM-KS
# devices are visible, the audio service is down, and nothing good will
# happen. Better to say so than to grab whatever is left and fail obscurely.

DEVICE = None
RATE = None

USABLE_APIS = ("WASAPI", "DirectSound", "MME")


def api_name(index):
    try:
        return sounddevice.query_hostapis(index)["name"]
    except Exception:
        return ""


def outputs():
    try:
        devices = sounddevice.query_devices()
    except Exception as error:
        print(f"Could not read the audio device list: {error}")
        return []
    return [
        (index, info)
        for index, info in enumerate(devices)
        if info.get("max_output_channels", 0) > 0
    ]


def pick_output():
    available = outputs()
    for wanted in USABLE_APIS:
        for index, info in available:
            if wanted.lower() in api_name(info["hostapi"]).lower():
                return index
    return None


def setup():
    global DEVICE
    DEVICE = pick_output()

    if DEVICE is None:
        print("\nAudio: no usable output device found.")
        print("Only kernel-streaming devices are visible, which means the")
        print("Windows audio service is down or still restarting.")
        print("Close this, wait until sound works in another app, and run again.\n")
        return None

    global RATE
    info = sounddevice.query_devices(DEVICE)
    RATE = int(info["default_samplerate"])
    print(f"Audio: device {DEVICE}, {info['name']}, via {api_name(info['hostapi'])}, {RATE} Hz")
    return DEVICE


def report():
    available = outputs()
    print(f"\nAudio devices visible to Python right now: {len(available)} outputs")
    for index, info in available:
        name = " ".join(str(info["name"]).split())
        print(f"  {index:>3}  {info['max_output_channels']} out  "
              f"{api_name(info['hostapi']):<20} {name}")
    print()

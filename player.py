import soundfile
import sounddevice
from effects import saturate

def play(path):
    data, samplerate = soundfile.read(path)
    data = saturate(data)
    sounddevice.play(data, samplerate)
    print("__________________________\n\nPress Enter to stop playback\n__________________________\n\n")
    while True:
        breaker = input()
        if breaker == "":
            sounddevice.stop()
            break
        else:
            print("\nInvalid input. Please press Enter to stop playback.\n\n")
            False
    sounddevice.wait()
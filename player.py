import soundfile
import sounddevice

def play(path):
    data, samplerate = soundfile.read(path)
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
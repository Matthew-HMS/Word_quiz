from gtts import gTTS
import subprocess

def speak(text):
    tts = gTTS(text=text, lang='en')
    filename = 'word.mp3'
    tts.save(filename)


def play_audio(filename):
    subprocess.run(['ffplay', '-nodisp', '-autoexit', filename])

speak("arbitrary")
filename = 'word.mp3'
play_audio(filename)
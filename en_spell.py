from gtts import gTTS
import subprocess
import random
import csv
import os
import threading

def speak(text):
    tts = gTTS(text=text, lang='en')
    filename = 'word.mp3'
    tts.save(filename)


def play_audio(filename):
    with open(os.devnull, 'w') as devnull:
        subprocess.run(['ffplay', '-nodisp', '-autoexit', filename], stdout=devnull, stderr=devnull)

study_set = {}
dataset = input("Which set you want to learn?  ")

# read csv file
with open(f'{dataset}.csv', mode ='r', encoding='utf-8')as file:
    csvFile = csv.reader(file)
    for row in csvFile:
        study_set[row[1]] = row[0]

keys = list(study_set.keys())
random.shuffle(keys)

# add options
for key in keys:
    word = key
    meaning = study_set[key]

    speak(meaning)
    response = input(f"What is the meaning of '{word}'?\n\n\n\n\n\n\nYour answer: ")

    if response == meaning:
        threading.Thread(target=play_audio, args=('word.mp3',)).start()
        print("Correct!\n")
        print("\033[1;37;42m ======================================================= \033[0m\n")
    else:
        print(f"Wrong! The correct answer is '{meaning}'.\n")
        while True:
            threading.Thread(target=play_audio, args=('word.mp3',)).start()
            retry = input("Please spell the word again ! ans: ")
            if retry == meaning:
                break
            print(f"Wrong! The correct answer is '{meaning}'. Try again.\n")
        keys.append(word)
        print("\033[1;37;41m ======================================================= \033[0m\n")
    
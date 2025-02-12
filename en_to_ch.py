from gtts import gTTS
import subprocess
import random
import csv
import os
import threading
import re

# add pronunciation
def speak(text):
    tts = gTTS(text=text, lang='en')
    filename = 'word.mp3'
    tts.save(filename)


def play_audio(filename):
    with open(os.devnull, 'w') as devnull:
        subprocess.run(['ffplay', '-nodisp', '-autoexit', filename], stdout=devnull, stderr=devnull)

def list_files(directory):
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    return sorted(files, key=lambda x: [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', x)])

def display_page(files, page, per_page):
    start = (page - 1) * per_page
    end = start + per_page
    print(f"\nPage {page}/{(len(files) + per_page - 1) // per_page}\n")
    for i, file in enumerate(files[start:end], start=1):
        print(f"{start + i}. {file}")
    

study_set = {}
per_page = 5

while True:
    try:
        files = list_files("./sets")
        total_pages = (len(files) + per_page - 1) // per_page
        page = 1

        while True:
            display_page(files, page, per_page)
            command = input("\nEnter file number to select, 'n' for next page, 'p' for previous page: ")

            if command.isdigit():
                file_index = int(command) - 1
                if 0 <= file_index < len(files):
                    dataset = files[file_index].rsplit('.', 1)[0]
                    break
                else:
                    print("Invalid file number. Please try again.\n")
            elif command.lower() == 'n':
                if page < total_pages:
                    page += 1
                else:
                    print("You are on the last page.\n")
            elif command.lower() == 'p':
                if page > 1:
                    page -= 1
                else:
                    print("You are on the first page.\n")
            else:
                print("Invalid command. Please try again.\n")

        file_path = f'./sets/{dataset}.csv'
        with open(file_path, encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                key = row[0]
                study_set[key] = row[1] 

        print(f"Set: {dataset}.csv loaded successfully!\n")
        break

    except FileNotFoundError:
        print("File not found. Please try again.\n")
        continue



keys = list(study_set.keys())
random.shuffle(keys)

# statistics
correct = 0
wrong = 0

# add options
for key in keys:

    word = key
    meaning = study_set[key]
    values = list(study_set.values())
    values.remove(meaning)
    random_values = random.sample(values, 3)
    possible_ans = [meaning] + random_values
    
    random.shuffle(possible_ans)
    question = {1:possible_ans[0].split(';')[0], 2:possible_ans[1].split(';')[0], 3:possible_ans[2].split(';')[0], 4:possible_ans[3].split(';')[0]}  # remove word after ;

    while True:
        try:
            speak(word)
            counter = f"({correct+wrong+1}/{len(keys)})"
            threading.Thread(target=play_audio, args=('word.mp3',)).start()
            response = input(f"What is the meaning of '{word}'? {counter}\n1. {question[1]}\n2. {question[2]}\n3. {question[3]}\n4. {question[4]}\n\n\n\n\n\nYour answer: ")

            if response not in ['1', '2', '3', '4']:
                raise ValueError("Invalid! Enter a number between 1 and 4.\n")

            if question[int(response)] == meaning.split(';')[0]:   # remove word after ;
                correct += 1
                print("Correct!\n")
                print("\033[1;37;42m ======================================================= \033[0m\n")
            else:
                print(f"Wrong! The correct answer is '{meaning}'.\n")
                wrong += 1
                while True:
                    threading.Thread(target=play_audio, args=('word.mp3',)).start()
                    retry = input(f"Please spell the word '{word}' ! ans: ")
                    if retry == word:
                        break
                    print("Wrong! Please try again.\n")
                keys.append(word) # wrong words should try again
                print("\033[1;37;41m ======================================================= \033[0m\n")
            break  # If no error, break the while loop and continue with the next key

        except ValueError as e:
            print(e)

# show statistics
print(f"Correct: {correct}\nWrong: {wrong}\nAccuracy: {round(correct/(correct+wrong),2)}\n")
input("Press 'Enter' to terminate the program...")

    
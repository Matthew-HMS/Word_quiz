from gtts import gTTS
import subprocess
import random
import csv
import os
import threading

# add pronunciation
def speak(text):
    tts = gTTS(text=text, lang='en')
    filename = 'word.mp3'
    tts.save(filename)


def play_audio(filename):
    with open(os.devnull, 'w') as devnull:
        subprocess.run(['ffplay', '-nodisp', '-autoexit', filename], stdout=devnull, stderr=devnull)

study_set = {}
while True:
    try:
        dataset = input("Which set you want to learn? (enter file's name) ")
        # read csv file
        with open(f'{dataset}.csv', mode ='r', encoding='utf-8')as file:
            csvFile = csv.reader(file)
            for row in csvFile:
                study_set[row[1]] = row[0]
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
    question = {1:possible_ans[0], 2:possible_ans[1], 3:possible_ans[2], 4:possible_ans[3]}

    while True:
        try:
            speak(meaning)
            counter = f"({correct+wrong+1}/{len(keys)})"
            response = input(f"What is the meaning of '{word}'? {counter}\n1. {question[1]}\n2. {question[2]}\n3. {question[3]}\n4. {question[4]}\n\n\n\n\n\nYour answer: ")
            

            if response not in ['1', '2', '3', '4']:
                raise ValueError("Invalid! Enter a number between 1 and 4.\n")
            
            if question[int(response)] == meaning:
                correct += 1
                # play_audio('word.mp3')
                print("Correct!\n")
                print("\033[1;37;42m ======================================================= \033[0m\n")
            else:
                print(f"Wrong! The correct answer is '{meaning}'.\n")
                wrong += 1
                while True:
                    threading.Thread(target=play_audio, args=('word.mp3',)).start()
                    retry = input("Please spell the word again ! ans: ")
                    if retry == meaning:
                        break
                    print(f"Wrong! The correct answer is '{meaning}'. Try again.\n")
                keys.append(word)
                print("\033[1;37;41m ======================================================= \033[0m\n")
            break
        
        except ValueError as e:
            print(e)


# show statistics
print(f"Correct: {correct}\nWrong: {wrong}\nAccuracy: {round(correct/(correct+wrong),2)}\n")

    
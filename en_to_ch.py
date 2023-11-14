import random
import csv

study_set = {}
dataset = input("Which set you want to learn?  ")

# read csv file
with open(f'{dataset}.csv', mode ='r', encoding='utf-8')as file:
    csvFile = csv.reader(file)
    for row in csvFile:
        study_set[row[0]] = row[1]

keys = list(study_set.keys())
random.shuffle(keys)

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
    response = input(f"What is the meaning of '{word}'?\n1. {question[1]}\n2. {question[2]}\n3. {question[3]}\n4. {question[4]}\n\n\n\n\n\nYour answer: ")

    if question[int(response)] == meaning:
        print("Correct!\n")
        print("\033[1;37;42m ======================================================= \033[0m\n")
    else:
        print(f"Wrong! The correct answer is '{meaning}'.\n")
        print("\033[1;37;41m ======================================================= \033[0m\n")

    

    
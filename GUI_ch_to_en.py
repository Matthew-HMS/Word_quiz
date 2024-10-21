import os
import csv
import random
import threading
import re
from tkinter import *
from tkinter import messagebox
from gtts import gTTS
import subprocess


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


def load_dataset():
    files = list_files("./sets")
    if files:
        selected_file.set(files[0])  
        menu = file_menu['menu']
        menu.delete(0, 'end') 
        for f in files:
            menu.add_command(label=f, command=lambda file=f: select_file(file))
    else:
        selected_file.set("no file")

def select_file(file):
    global dataset, study_set
    dataset = file
    study_set.clear()
    
    try:
        file_path = f'./sets/{dataset}'
        with open(file_path, encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                key = row[1]
                study_set[key] = row[0] 
        messagebox.showinfo("Success", f"sets '{dataset}' has loaded！")
        start_quiz()  
    except FileNotFoundError:
        messagebox.showerror("Error", "can't find the file")

def start_quiz():
    global keys, correct, wrong, current_word, current_meaning
    keys = list(study_set.keys())
    random.shuffle(keys)
    correct = 0
    wrong = 0
    show_next_word()

def show_next_word():
    global current_word, current_meaning
    if keys:
        current_word = keys.pop(0)
        current_meaning = study_set[current_word]
        
        values = list(study_set.values())
        values.remove(current_meaning)
        random_values = random.sample(values, 3)
        possible_ans = [current_meaning] + random_values
        random.shuffle(possible_ans)

        question_label.config(text=f"What is the meaning of '{current_word.split(';')[0]}'?")
        for i, option in enumerate(possible_ans):
            options[i].config(text=option)
        
        speak(current_meaning)
        # threading.Thread(target=play_audio, args=('word.mp3',)).start()
    else:
        show_stats()

def check_answer(selected_option):
    global correct, wrong
    if options[selected_option]['text'] == current_meaning:
        correct += 1
        play_audio('word.mp3')
        # messagebox.showinfo("Correct", "Correct!")
        show_next_word()
    else:
        wrong += 1
        messagebox.showerror("Wrong", f"Wrong! The answer is:'{current_meaning}'")
        keys.append(current_word)
        play_audio('word.mp3')
        show_retry_entry()   

retry_entry = None
retry_button = None

def show_retry_entry():
    global retry_entry, retry_button
    disable_options()  # 禁用選項按鈕
    if retry_entry is None:  # 如果輸入框不存在，創建一個
        retry_entry = Entry(root, width=50)
    retry_entry.pack(pady=5)  # 每次答錯都會顯示輸入框

    if retry_button is None:  # 如果確認按鈕不存在，創建一個
        retry_button = Button(root, text="OK", command=check_retry_entry)
    retry_button.pack(pady=5)  # 每次答錯都會顯示按鈕

    retry_entry.delete(0, END)  # 清空之前的輸入
    retry_entry.focus_set()  # 將焦點設置到輸入框上


# 檢查用戶的拼寫
def check_retry_entry():
    user_input = retry_entry.get()
    if user_input == current_meaning:  # 如果拼寫正確
        # messagebox.showinfo("Correct", "Correct!")
        retry_entry.pack_forget()  # 隱藏輸入框
        retry_button.pack_forget()  # 隱藏按鈕
        enable_options()  # 啟用選項按鈕
        show_next_word()  # 顯示下一個單詞
    else:
        messagebox.showerror("Wrong", f"Wrong！Please insert again: '{current_meaning}'")
        retry_entry.delete(0, END)  # 清空輸入框，讓使用者再試一次
        retry_entry.focus_set()  # 讓輸入框繼續有焦點
        play_audio('word.mp3')  
        
        
def disable_options():
    """禁用所有選項按鈕"""
    for option in options:
        option.config(state="disabled")

def enable_options():
    """啟用所有選項按鈕"""
    for option in options:
        option.config(state="normal")

def show_stats():
    accuracy = round(correct / (correct + wrong), 2) if (correct + wrong) > 0 else 0
    messagebox.showinfo("Statistic", f"Correct: {correct}\nWrong: {wrong}\n:Accuracy: {accuracy}")

# GUI
root = Tk()
root.title("word quiz")

dataset = ""
study_set = {}
keys = []
correct = 0
wrong = 0
current_word = ""
current_meaning = ""

# 文件選擇
frame = Frame(root)
frame.pack(pady=10)
file_label = Label(frame, text="Select a set:", font=("Arial", 12))
file_label.pack(side=LEFT)

# 創建 OptionMenu 
selected_file = StringVar()
files = list_files("./sets")
selected_file.set(files[0] if files else "no file")  # set default value

file_menu = OptionMenu(frame, selected_file, *files)
file_menu.pack(side=LEFT)

# 加載按鈕
load_button = Button(frame, text="OK", command=lambda: select_file(selected_file.get()), font = ("Arial",10))
load_button.pack(side=LEFT)

# 問題標籤
question_label = Label(root, text="loading questions...", font=("Arial", 16))
question_label.pack(pady=20)

# 選項按鈕
options = []
for i in range(4):
    option = Button(root, text="", width=50, command=lambda i=i: check_answer(i))
    option.pack(pady=5)
    options.append(option)

root.mainloop()

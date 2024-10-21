import os
import csv
import random
import threading
import re
from tkinter import *
from tkinter import messagebox
from gtts import gTTS
import subprocess

# 播放單詞發音
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
        file_menu['menu'].delete(0, 'end')  # 清除舊的選項
        for f in files:
            file_menu['menu'].add_command(label=f, command=lambda file=f: select_file(file))
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
        messagebox.showinfo("Success", f"set '{dataset}' is loaded！")
        start_quiz()  
    except FileNotFoundError:
        messagebox.showerror("Wrong", "no file found")

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
        
        # 顯示當前問題
        question_label.config(text=f"What is the meaning of '{current_word.split(';')[0]}'?")
        
        # 播放發音
        speak(current_meaning)
        # threading.Thread(target=play_audio, args=('word.mp3',)).start()
    else:
        show_stats()

def check_answer():
    global correct, wrong
    user_input = answer_entry.get()
    answer_entry.delete(0, END)
    if user_input == current_meaning:
        correct += 1
        # messagebox.showinfo("Correct", "Correct!")
        play_audio('word.mp3')
        enable_normal_answer_mode()
        show_next_word()  # 繼續下一個問題
    else:
        wrong += 1
        messagebox.showerror("Wrong", f"Wrong！Correct answer is：'{current_meaning}'")
        play_audio('word.mp3')
        keys.append(current_word)  # 將錯誤的單詞放回題庫
        retry_entry.pack(pady=5)
        retry_button.pack(pady=5)
        answer_entry.config(state="disabled")
        enable_retry_mode()

def retry_answer():
    retry_input = retry_entry.get()
    retry_entry.delete(0, END)
    if retry_input == current_meaning:
        # messagebox.showinfo("Correct", "Correct!")
        retry_entry.pack_forget()
        retry_button.pack_forget()
        answer_entry.config(state="normal")
        enable_normal_answer_mode() 
        show_next_word()
    else:
        messagebox.showerror("Wrong", f"Wrong!Insert again: '{current_meaning}'")
        play_audio('word.mp3')
        

def show_stats():
    accuracy = round(correct / (correct + wrong), 2) if (correct + wrong) > 0 else 0
    messagebox.showinfo("Statistic", f"Correct: {correct}\nWrong: {wrong}\nAccuracy: {accuracy}")
    
def enable_normal_answer_mode():
    root.unbind('<Return>')  # 解除 retry_answer 的綁定
    root.bind('<Return>', lambda event: check_answer())  # 綁定 Enter 到 check_answer

def enable_retry_mode():
    root.unbind('<Return>')  # 解除 check_answer 的綁定
    root.bind('<Return>', lambda event: retry_answer())  # 綁定 Enter 到 retry_answer


# GUI佈局
root = Tk()
root.title("word quiz")
root.bind('<Return>', lambda event: check_answer())  # 綁定 Enter 到 check_answer

dataset = ""
study_set = {}
keys = []
correct = 0
wrong = 0
current_word = ""
current_meaning = ""

# 文件選擇框
frame = Frame(root)
frame.pack(pady=10)
file_label = Label(frame, text="Select set:")
file_label.pack(side=LEFT)

# 創建 OptionMenu 控件
selected_file = StringVar()
files = list_files("./sets")
selected_file.set(files[0] if files else "no file")  # 設置默認值

file_menu = OptionMenu(frame, selected_file, *files)
file_menu.pack(side=LEFT)

# 加載數據集按鈕
load_button = Button(frame, text="loading set", command=lambda: select_file(selected_file.get()))
load_button.pack(side=LEFT)

# 問題顯示
question_label = Label(root, text="loading question...", font=("Arial", 16))
question_label.pack(pady=20)

# 答案輸入框
answer_entry = Entry(root, width=50)
answer_entry.pack(pady=5)

# 確認答案按鈕
check_button = Button(root, text="OK", command=check_answer)
check_button.pack(pady=5)

# 重試輸入框
retry_entry = Entry(root, width=50)
retry_button = Button(root, text="重試拼寫", command=retry_answer)

root.mainloop()

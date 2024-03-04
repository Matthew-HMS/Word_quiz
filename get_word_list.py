import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import csv

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
driver.get("https://quizlet.com/tw/857640181/%E6%89%98%E7%A6%8F%E5%88%86%E9%A1%9E%E5%AD%97%E5%BD%9903-anthropologyarchaeology-flash-cards/?new")

word_list = driver.find_elements(By.XPATH, "//*[@class='SetPageTerm-wordText']")
definition_list = driver.find_elements(By.XPATH, "//*[@class='SetPageTerm-definitionText']")

words = []
definitions = []
for word in word_list:
    words.append(word.text)

for definition in definition_list:
    definitions.append(definition.text)

word_dict = dict(zip(words, definitions))

# Specify the file name
filename = './sets/toefl_anthropology.csv'
with open(filename, 'w', newline='', encoding='utf-8') as csv_file:  
    writer = csv.writer(csv_file)
    # Write the data
    for key, value in word_dict.items():
       cleaned_key = key.replace('\n', '; ')
       cleaned_key = cleaned_key.replace(',', '，')
       cleaned_value = value.replace('\n', '; ')
       cleaned_value = cleaned_value.replace(',', '，')
       writer.writerow([cleaned_key, cleaned_value])


time.sleep(3)
driver.quit()
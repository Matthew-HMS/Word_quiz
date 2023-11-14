import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import csv

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
driver.get("https://quizlet.com/fr/414376231/mason-gre-2000-20-flash-cards/?funnelUUID=7353b11b-d308-48b3-829c-c757986b9dbd")

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
filename = 'mason_gre20.csv'
with open(filename, 'w', newline='', encoding='utf-8') as csv_file:  
    writer = csv.writer(csv_file)
    # Write the data
    for key, value in word_dict.items():
       cleaned_key = key.replace('\n', ';')
       cleaned_value = value.replace('\n', ';')
       writer.writerow([cleaned_key, cleaned_value])


time.sleep(3)
driver.quit()
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time


driver = Driver(browser='chrome', headless=False, uc=True)
wait = WebDriverWait(driver, 10)  # Wait up to 10 seconds

driver.get("https://quizlet.com/tw/874939072/mason-2000-flash-cards/")

while True:
    try:
        button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@class='AssemblyButtonBase AssemblyTextButton AssemblyTextButton--secondary AssemblyButtonBase--large AssemblyButtonBase--padding']")))
        button.click()
        time.sleep(3)
    except:
        break

word_list = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[@class='TermText notranslate lang-en']")))
definition_list = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[@class='TermText notranslate lang-zh-TW']")))

words = [word.text for word in word_list]
definitions = [definition.text for definition in definition_list]

word_dict = dict(zip(words, definitions))

# Specify the file name
filename = './sets/test2.csv'
with open(filename, 'w', newline='', encoding='utf-8') as csv_file:  
    writer = csv.writer(csv_file)
    # Write the data
    for key, value in word_dict.items():
       cleaned_key = key.replace('\n', '; ').replace(',', '，')
       cleaned_value = value.replace('\n', '; ').replace(',', '，')
       writer.writerow([cleaned_key, cleaned_value])

time.sleep(3)
driver.quit()
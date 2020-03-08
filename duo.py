#!/usr/bin/env python

URL = "https://www.duolingo.com/"
BRAIN_CSV = "brain.csv"
UPDATE_BRAIN = True
CONFIG_FILE = "config.yml"

import time, sys, csv, unicodedata, os, datetime
import yaml
import pdb
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

# Load username and password from config file
with open(CONFIG_FILE, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)
USERNAME = cfg['username']
PASSWORD = cfg['password']

def lookup_answer(brain, question):
    ans = None
    for line in brain:
        if line['ar'] == question:
            ans = line['en']
        elif line['en'] == question:
            ans = line['ar']
    return ans
def update_brain(brain):
    print('Saving brain file.')
    # Save off the existing file, just in case
    d = datetime.datetime.today()
    timestamp = d.strftime("%Y%m%d_%H%M%S")
    newname = "%s-%s.bak" % (BRAIN_CSV, timestamp)
    os.rename(BRAIN_CSV, newname) 
    print('Existing brain backed up to: %s' % newname)
    # Output the contents of the in-memory brain to csv
    with open(BRAIN_CSV, 'w') as brainfile:
        for line in brain:
            brainfile.write("%s,%s\n" % (line['en'], line['ar']))
def get_progress():
    return driver.find_element_by_css_selector('._1TkZD').get_attribute('style').split()[-1][:-1] # Get last style (width), shave off the semicolon
def next_question(current_progress):
    while True:
        driver.find_element_by_css_selector('button[data-test="player-next"]').click()
        time.sleep(0.2)
        new_progress = get_progress()
        if current_progress != new_progress:
            break

# Build the "brain" to allow O(1) lookup
print("Building brain...")
brain = []
with open(BRAIN_CSV) as brainfile:
    for line in brainfile:
        data = line.rstrip().split(',')
        # Unicodedata normalize NFKD: Map logically equiv chars (such as arabic inital, middle, and end forms, capital letters, japanese kana, etc.)
        brain.append({'en':data[0],'ar':unicodedata.normalize('NFKD',data[1])})
#with open(BRAIN_CSV, encoding='utf-8-sig') as csvfile:
#    reader = csv.DictReader(csvfile)
#    for row in reader:
#        brain.append(row)
print("Done.")

driver = webdriver.Firefox()

driver.get(URL)

elem = driver.find_element_by_xpath("//a[text()[contains(.,'I ALREADY HAVE AN ACCOUNT')]]")
elem.click()

elem = driver.find_element_by_xpath("//input[@placeholder='Email or username']")
elem.send_keys(USERNAME)
elem = driver.find_element_by_xpath("//input[@placeholder='Password']")
elem.send_keys(PASSWORD)

elem = driver.find_element_by_xpath("//button[@type='submit' and contains(text(),'Log in')]")
elem.click()

time.sleep(5)

# Logged in.

lang_icon = driver.find_element_by_css_selector("._3gtu3._1-Eux.iDKFi")
lang_icon.click()
lang_name = driver.find_element_by_css_selector(".U_ned").text

print("Currently learning: %s" % lang_name)

print("Available skills:")
skills = driver.find_elements_by_xpath("//div[@data-test='skill']")
for skill in skills:
    text_node = skill.find_element_by_xpath("./div/div/div[position()=2]") # lesson name
    print(text_node.text + ", ", end="")
print()

skill_icons = driver.find_elements_by_xpath("//div[@data-test='skill-icon']")

skill_icons[3].click()
start_button = driver.find_element_by_xpath("//button[@data-test='start-button']")
start_button.click()

time.sleep(2)

learning_title = driver.find_element_by_css_selector('h2.nyHZG')
print("Lesson title: %s" % learning_title.text)

print("Starting lesson.")
driver.find_element_by_css_selector('button[data-test="player-next"]').click()

# For each question
for i in range(0,999):
    progress = get_progress() 
    print("Progress: %s" % progress)
    # Check if we're done
    done_check = driver.find_elements_by_css_selector('h1[data-test="answers-correct"]')
    if len(done_check) > 0:
        break

    try:
        prompt = driver.find_element_by_css_selector('h1[data-test="challenge-header"] span').text
    except NoSuchElementException:
        prompt = None
        # Continue to next question
        next_question(progress)
        continue
    print("Prompt: %s" % prompt)
    
    if prompt == "What sound does this make?":
        q = driver.find_element_by_css_selector('span[dir="rtl"]').text
        elem_a = driver.find_elements_by_css_selector('div[data-test="challenge-judge-text"]')
    elif prompt.startswith("Select the correct character(s) for"):
        q = prompt.split()[-1][1:-1] # get the last word, remove quotation marks 
        elem_a = driver.find_elements_by_css_selector('label[data-test="challenge-choice-card"] div:first-child span[dir="rtl"]')
    elif prompt == "Match the pairs":
        elem_tap = driver.find_elements_by_css_selector('button[data-test="challenge-tap-token"]')
        tapped = 0
        for elem1 in elem_tap:
            print("Tap questions: %s" % [x.text for x in elem_tap])
            try:
                if elem1.is_enabled() == False or tapped >= len(elem_tap) // 2:
                    continue
            except StaleElementReferenceException:
                break
            elem1_ans = lookup_answer(brain, elem1.text)
            if elem1_ans is None:
                print("Answer not known: %s" % elem1.text)
                elem1_ans = input("Enter the answer: ")
                brain.append({'en':elem1.text,'ar':elem1_ans})
            elem1.click()
            for elem2 in elem_tap:
                if elem2.text == elem1_ans:
                    elem2.click()
                    tapped += 1
                    break
        # Done tapping! :)
        next_question(progress)
        continue
    print("Question: %s" % q)
    print("Answers: %s" % [x.text for x in elem_a])

    # Search for match
    match = False
    n1 = unicodedata.normalize('NFKD', q)
    ans = lookup_answer(brain, n1)

    if ans == None:
        print("Answer not known.")
        ans = input("Enter the answer: ")
        brain.append({'en':n1,'ar':ans})
    for elem in elem_a:
        if elem.text == ans:
            elem.click()
            break

    # Submit answer
    driver.find_element_by_css_selector('button[data-test="player-next"]').click()
    # Continue to next question
    next_question(progress)

# Acknowledge end of lesson
driver.find_element_by_css_selector('button[data-test="player-next"]').click()
# No thanks to plus
driver.find_element_by_css_selector('button[data-test="no-thanks-to-plus"]').click()
if UPDATE_BRAIN:
    update_brain(brain)

#driver.close()


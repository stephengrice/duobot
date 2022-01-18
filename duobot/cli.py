import os
import time
import yaml
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
CFG_FILE = os.path.join(REPO_ROOT, 'config', 'config.yml')
LOGIN_URL = "https://www.duolingo.com/"

BRAIN_CHINESE = os.path.join(REPO_ROOT, 'brain', 'Chinese.csv')
BRAIN_SEP = "|"

def get_brain():
    result = []
    with open(BRAIN_CHINESE, 'r') as f:
        for line in f:
            result.append(line.split(BRAIN_SEP))
    return result

def search_brain(brain, query):
    answers = []
    for row in brain:
        if row[0] == query:
            answers.append(row[1])
        elif row[1] == query:
            answers.append(row[0])
    return answers

def main():
    brain = get_brain()
    options = webdriver.firefox.options.Options()
    # if not DEBUG or ci: options.headless = True
    driver = webdriver.Firefox(log_path='geckodriver.log', options=options)
    driver.implicitly_wait(5)
    driver.get(LOGIN_URL)
    driver.find_element_by_css_selector("[data-test='have-account']").click()
    driver.find_element_by_css_selector("[data-test='email-input']").send_keys(os.environ['DUOBOT_USERNAME'])
    driver.find_element_by_css_selector("[data-test='password-input']").send_keys(os.environ['DUOBOT_PASSWORD'])
    driver.find_element_by_css_selector("[data-test='register-button']").click()
    driver.find_element_by_css_selector("[data-test='skill-icon']").click()
    driver.find_element_by_css_selector("[data-test='start-button']").click()

    while True:
        try:
            header = driver.find_element_by_css_selector("[data-test='challenge-header']").text
            print("Header: %s" % header)
            if 'Select the correct character' in header:
                prompt = header.split("“")[1].split("”")[0]
            else:
                prompt = driver.find_element_by_css_selector("div[dir='ltr'],span[dir='ltr']").text
            prompt = prompt.lower()
            for filter_char in ['!', '.', '?', u'\uFF01']:
                prompt = prompt.lower().replace(filter_char, '')
            print("Prompt: %s" % prompt)
            answers = search_brain(brain, prompt)
            print("Found answers: %s" % answers)
            for btn in driver.find_elements_by_css_selector("[data-test='challenge-tap-token']"):
                print("Checking btn %s" % btn.text)
                if btn.text in answers:
                    print("clicking")
                    btn.click()
            for btn in driver.find_elements_by_css_selector("[data-test='challenge-judge-text']"):
                print("Checking 'challenge-judge-text' %s" % btn.text)
                if btn.text in answers:
                    print("clicking")
                    btn.click()
            for btn in driver.find_elements_by_css_selector("[data-test='challenge-choice-card'] div:first-child"):
                print("Checking 'challenge-choice-card' %s" % btn.text)
                if btn.text in answers:
                    print("clicking")
                    btn.click()
            textarea = driver.find_element_by_css_selector("[data-test='challenge-translate-input'")
            textarea.send_keys(answers[0]) # TODO detect which it's asking for - english or chinese
        except NoSuchElementException:
            print("No such element")
        driver.find_element_by_css_selector("[data-test='player-next']").click()
        driver.find_element_by_css_selector("[data-test='player-next']").click()
        print("----- sleeping -----")
        time.sleep(3)
import os
import time
import yaml
from selenium import webdriver

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
    for row in brain:
        if row[0] == query:
            return row[1]
        elif row[1] == query:
            return row[0]
    return None

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
    prompt = driver.find_element_by_css_selector("div[dir='ltr']").text
    prompt = prompt.lower().replace('!','').replace('.','').replace('?','')
    print(prompt)
    answer = search_brain(brain, prompt)
    print("Found answer: %s" % answer)
    for btn in driver.find_elements_by_css_selector("[data-test='challenge-tap-token']"):
        print("Checking btn %s" % btn.text)
        if btn.text == answer:
            print("clicking")
            btn.click()
    driver.find_element_by_css_selector("[data-test='player-next']").click()
    driver.find_element_by_css_selector("[data-test='player-next']").click()
    while True:
        time.sleep(1)
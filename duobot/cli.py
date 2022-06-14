import os
import time
import yaml
from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
CFG_FILE = os.path.join(REPO_ROOT, 'config', 'config.yml')
LOGIN_URL = "https://www.duolingo.com/"

BRAIN_CHINESE = os.path.join(REPO_ROOT, 'brain', 'Chinese.csv')
BRAIN_ARABIC = os.path.join(REPO_ROOT, 'brain', 'Arabic.csv')
BRAIN_SEP = "|"

def get_brain():
    result = []
    with open(BRAIN_ARABIC, 'r') as f:
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
            elif 'What do you hear?' in header:
                # skip it
                print("Listening not supported")
                print("Skipping")
                driver.find_element_by_css_selector('button[data-test=player-skip]').click()
                driver.find_element_by_css_selector('button[data-test=player-next]').click()
                continue
            elif 'What sound does this make?' in header:
                prompt = driver.find_element_by_css_selector('span[dir=rtl]').text
            elif 'Select the matching pairs' in header:
                pairs = driver.find_elements_by_css_selector('[data-test="challenge-tap-token-text"]')
                for p1 in pairs:
                    ans = search_brain(brain, p1.text)[0]
                    p1.click()
                    print("Clicked p1:",p1.text)
                    for p2 in pairs:
                        print("Checking right pair:", p2.text, 'for', ans)
                        if p2.text == ans:
                            print("Clicked p2:",p2.text)
                            p2.click()
                driver.find_element_by_css_selector("[data-test='player-next']").click()
                driver.find_element_by_css_selector("[data-test='player-next']").click()
                continue
            else:
                prompt = driver.find_element_by_css_selector("div[dir='ltr'],span[dir='ltr']").text
            prompt = prompt.lower()
            for filter_char in ['!', '.', '?', u'\uFF01']:
                prompt = prompt.lower().replace(filter_char, '')
            print("Prompt: %s" % prompt)
            answers = search_brain(brain, prompt)
            print("Found answers: %s" % answers)
            for btn in driver.find_elements_by_css_selector("[data-test='challenge-tap-token'], [data-test='challenge-choice'] span[dir=rtl], [data-test='challenge-judge-text'],[data-test='challenge-choice-card'] div:first-child"):
                print("Checking btn %s" % btn.text)
                if btn.text in answers:
                    print("clicking")
                    btn.click()
            # print("Attempting to type answer")
            # textarea = driver.find_element_by_css_selector("[data-test='challenge-translate-input]'")
            # textarea.send_keys(answers[0]) # TODO detect which it's asking for - english or chinese
        except NoSuchElementException as e:
            print(e.msg)
        except StaleElementReferenceException as e:
            print(e.msg)
        except ElementClickInterceptedException as e:
            print(e.msg)
        driver.find_element_by_css_selector("[data-test='player-next']").click()
        time.sleep(0.5)
        driver.find_element_by_css_selector("[data-test='player-next']").click()
        print("----- sleeping -----")
        time.sleep(1)
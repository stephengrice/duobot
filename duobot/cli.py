import os
import time
import yaml
from selenium import webdriver

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
CFG_FILE = os.path.join(REPO_ROOT, 'config', 'config.yml')
LOGIN_URL = "https://www.duolingo.com/"


def main():
    config = yaml.load(CFG_FILE, yaml.SafeLoader)
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
    print("searching for prompt...")
    prompt = driver.find_element_by_css_selector("[dir=ltr]").text
    print(prompt)
    print("printed prompt")
    breakpoint()
    while True:
        print("sleeping")
        time.sleep(1)
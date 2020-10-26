import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import util
from brain import Brain

LOGIN_URL = "https://www.duolingo.com/"
BASIC_ARABIC_URL = "https://www.duolingo.com/skill/ar/Alphabet1/practice"
TMP_DIR = "tmp"

class DuoBot2:
    def __init__(self):
        options = webdriver.firefox.options.Options()
        # if not DEBUG or ci: options.headless = True
        self.driver = webdriver.Firefox(service_log_path='%s/geckodriver.log' % TMP_DIR, options=options)
        self.driver.implicitly_wait(util.get_config()['webdriver_wait'])
        self.logged_in = False
        self.brain = Brain('Arabic')
    def login(self):
        try:
            # Open up the page
            self.driver.get(LOGIN_URL)
            # Click "I already have an account"
            elem = self.driver.find_element_by_xpath("//a[text()[contains(.,'I ALREADY HAVE AN ACCOUNT')]]")
            elem.click()
            # Type the username
            elem = self.driver.find_element_by_xpath("//input[@placeholder='Email or username']")
            elem.send_keys(util.get_config()['username'])
            # Type the password
            elem = self.driver.find_element_by_xpath("//input[@placeholder='Password']")
            elem.send_keys(util.get_config()['password'])
            # Hit enter to login
            elem.send_keys(Keys.RETURN)
            self.logged_in = True
        finally:
            pass
    def basic_arabic_lesson(self):
        self.driver.get(BASIC_ARABIC_URL)
        time.sleep(1)
        for _ in range(100):
            self.act()
            time.sleep(0.5)
    def act(self):
        lesson_state = util.get_lesson_state(self.driver)
        print('lesson state:',lesson_state)
        if lesson_state == util.LessonState.LESSON_QUESTION:
            question_state = util.get_question_state(self.driver)
            print('question state:',question_state)
            if question_state == util.QuestionState.ANSWER_CORRECT:
                util.click_next(self.driver)
            elif question_state == util.QuestionState.LISTENING:
                util.click_skip(self.driver)
                util.click_next(self.driver)
            else:
                q = util.get_question(self.driver, question_state)
                if q is not None:
                    ans = self.brain.lookup_answer(q)
                    util.click_answer(self.driver, question_state, ans)
                    util.click_next(self.driver)
                else:
                    print('tap?')
        elif lesson_state == util.LessonState.UNKNOWN:
            util.click_next(self.driver)

if __name__ == '__main__':
    bot = DuoBot2()
    bot.login()
    time.sleep(3)
    bot.basic_arabic_lesson()

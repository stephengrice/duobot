import time
import random

import unicodedata

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

import util
from brain import Brain

LOGIN_URL = "https://www.duolingo.com/"
BASIC_ARABIC_URL = "https://www.duolingo.com/skill/ar/Alphabet1/practice"
BASIC_CHINESE_URL = "https://www.duolingo.com/skill/zs/Greeting/practice"
TMP_DIR = "tmp"

class DuoBot2:
    def __init__(self):
        options = webdriver.firefox.options.Options()
        options.headless = False
        self.driver = webdriver.Firefox(service_log_path='%s/geckodriver.log' % TMP_DIR, options=options)
        self.driver.implicitly_wait(util.get_config()['webdriver_wait'])
        self.logged_in = False
        self.brain = Brain('Chinese')
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
    def basic_chinese_lesson(self):
        self.driver.get(BASIC_CHINESE_URL)
        time.sleep(1)
        for _ in range(100):
            lesson_state = util.get_lesson_state(self.driver)
            if lesson_state == util.LessonState.LESSON_PLUS:
                break
            self.act(lesson_state)
            time.sleep(0.5)
    def act(self, lesson_state):
        try:
            print('lesson state:',lesson_state)
            if lesson_state == util.LessonState.LESSON_QUESTION:
                question_state = util.get_question_state(self.driver)
                print('question state:',question_state)
                if question_state == util.QuestionState.ANSWER_CORRECT:
                    util.click_next(self.driver)
                elif question_state == util.QuestionState.LISTENING:
                    util.click_skip(self.driver)
                    util.click_next(self.driver)
                elif question_state == util.QuestionState.MATCH_PAIRS:
                    matches = util.get_answer_elems(self.driver, question_state)
                    print('Matching')
                    for elem in matches:
                        ans = self.brain.lookup_answer(elem.text)
                        print("clicking",ans)
                        if util.click_answer(self.driver, question_state, ans):
                            elem.click()
                    util.click_next(self.driver)
                elif question_state == util.QuestionState.WRITE_IN:
                    print("Write-in")
                    q = util.get_question(self.driver, question_state)
                    ans = self.brain.lookup_answer(q)
                    util.toggle_keyboard(self.driver)
                    elem = util.get_elem(self.driver, util.CSS_WRITE_IN)
                    elem.send_keys(ans)
                    util.click_next(self.driver)
                    util.click_next(self.driver)
                elif question_state == util.QuestionState.SELECT_CHARACTERS:
                    print("Select Characters")
                    q = util.get_question(self.driver, question_state)
                    ans = self.brain.lookup_answer(q)
                    matches = util.get_answer_elems(self.driver, question_state)
                    for m in matches:
                        if m.text == ans:
                            m.click()
                    util.click_next(self.driver)
                    util.click_next(self.driver)
                elif question_state == util.QuestionState.SELECT_SOUND:
                    print("Select Sound")
                    q = util.get_question(self.driver, question_state)
                    ans = self.brain.lookup_answer(q)
                    matches = util.get_answer_elems(self.driver, question_state)
                    for m in matches:
                        if unicodedata.normalize('NFKD', m.text) == unicodedata.normalize('NFKD', ans):
                            print("clicked matching sound")
                            m.click()
                    util.click_next(self.driver)
                    util.click_next(self.driver)
                else:
                    q = util.get_question(self.driver, question_state)
                    if q is not None:
                        ans = self.brain.lookup_answer(q)
                        ans_clicked = util.click_answer(self.driver, question_state, ans)
                        if ans_clicked:
                            util.click_next(self.driver)
                        else:
                            # Guess we don't know this one
                            # Pick one randomly
                            answers = util.get_answers(self.driver, question_state)
                            clicked = util.click_answer(self.driver, question_state, random.choice(answers))
                            # TODO learn from correct answer if not right
                            # TODO somehow store what we tried so we don't make the same mistakes
                            util.click_next(self.driver)
                    else:
                        print('Unknown question type or something like that')
            elif lesson_state == util.LessonState.LESSON_PLUS:
                util.click_next(self.driver)
            elif lesson_state == util.LessonState.UNKNOWN:
                util.click_next(self.driver)
        except:
            pass
if __name__ == '__main__':
    bot = DuoBot2()
    bot.login()
    time.sleep(3)
    bot.basic_chinese_lesson()
    bot.driver.close()

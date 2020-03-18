#!/usr/bin/env python

URL = "https://www.duolingo.com/"
BRAIN_FILE = "brain.csv"
UPDATE_BRAIN = True
CONFIG_FILE = "config.yml"
COOKIES_FILE = "cookies.json"
SLEEP_NEXT_QUESTION = 0.5 # seconds
DEBUG = True

CSS_CLASS_HEADER = '._1KHTi._1OomF'
CSS_CLASS_LANG_ICON = '._3gtu3._1-Eux.iDKFi'
CSS_CLASS_LANG_NAME = '.U_ned'
CSS_CLASS_NEXT_ENABLED = '_2VaJD'
CSS_SELECTOR_LESSON_START = 'h2.nyHZG'
CSS_SELECTOR_LESSON_MID = 'div._3bFAF._34-WZ._27r1x._3xka6'
CSS_SELECTOR_LESSON_END = 'h2[data-test="answers-correct"]'

NATIVE_LANG = "English"
FOREIGN_LANG = "Arabic"

import time, sys, csv, unicodedata, os, datetime
import yaml
import pdb
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException, ElementNotInteractableException


def load_config():
    # Load username and password from config file
    with open(CONFIG_FILE, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg
def build_brain():
    brain = []
    with open(BRAIN_FILE) as brainfile:
        for line in brainfile:
            data = line.rstrip().split(',')
            # Unicodedata normalize NFKD: Map logically equiv chars (such as arabic inital, middle, and end forms, capital letters, japanese kana, etc.)
            add_to_brain(brain, data[0], data[1], data[2], data[3], False)
    return brain
def solicit_user_answer(question, options):
    print("Answer not known.")
    print("Question: %s" % question)
    print("Answers:")
    for i, opt in enumerate(options):
        print("%d) %s" % (i+1,opt))
    userans = -1
    while userans < 1 or userans >= len(options) + 1:
        try:
            userans = int(input("Enter the correct number: "))
        except ValueError:
            userans = -1
    print("You chose: %s" % options[userans - 1])
    return options[userans - 1]
def lookup_answer(brain, question):
    # Perform unicode normalization
    question = unicodedata.normalize('NFKD', question)
    ans = None
    for line in brain:
        if line['p1'] == question:
            ans = line['p2']
        elif line['p2'] == question:
            ans = line['p1']
    return ans
def update_brain(brain):
    # TODO only append new stuff. Check if exists already before append to file
    print('Saving brain file.')
    # Save off the existing file, just in case
    d = datetime.datetime.today()
    timestamp = d.strftime("%Y%m%d_%H%M%S")
    newname = "brain-%s.bak.csv" % (timestamp)
    os.rename(BRAIN_FILE, newname)
    print('Existing brain backed up to: %s' % newname)
    # Output the contents of the in-memory brain to csv
    with open(BRAIN_FILE, 'w') as brainfile:
        for line in brain:
            brainfile.write("%s,%s,%s,%s\n" % (line['p1'], line['p2'], line['language'], line['lesson']))
def add_to_brain(brain, phrase1, phrase2, language, lesson, update_brain_check=UPDATE_BRAIN):
    # print("Adding to brain: %s,%s,%s,%s" % (phrase1, phrase2, language, lesson))
    brain.append({'p1':unicodedata.normalize('NFKD',phrase1),'p2':unicodedata.normalize('NFKD',phrase2), 'language':language, 'lesson': lesson})
    if update_brain_check:
        update_brain(brain)

class DuoBot:
    def __init__(self):
        self.driver = webdriver.Firefox()
        self.brain = build_brain()
        self.cfg = load_config()
        #
        self.driver.implicitly_wait(self.cfg['webdriver_wait'])
        #
        self.logged_in = False
        self.current_language = None
        self.current_lesson = None
        self.skills = None
    def __del__(self):
        if not DEBUG:
            self.driver.close()
    def perform_login(self):
        """ Perform login to DuoLingo website
        Precondition: Not logged in, browser is closed
        Postcondition: Logged in, driver is at '/learn'
        Returns:
            True if successful login
            False if login failed
        """
        # Open up the page
        self.driver.get(URL)
        # Check if login possible with cookies
        if os.path.exists(COOKIES_FILE): # TODO check if cookies expired
            with open(COOKIES_FILE) as f:
                cookies = json.load(f)
                for c in cookies:
                    self.driver.add_cookie(c)
            # Open up the page (now with cookies)
            self.driver.get(URL)
        else:
            # Click "I already have an account"
            elem = self.driver.find_element_by_xpath("//a[text()[contains(.,'I ALREADY HAVE AN ACCOUNT')]]")
            elem.click()
            # Type the username
            elem = self.driver.find_element_by_xpath("//input[@placeholder='Email or username']")
            elem.send_keys(self.cfg['username'])
            # Type the password
            elem = self.driver.find_element_by_xpath("//input[@placeholder='Password']")
            elem.send_keys(self.cfg['password'])
            # Click login
            elem = self.driver.find_element_by_xpath("//button[@type='submit' and contains(text(),'Log in')]")
            elem.click()
        # Success: URL is correct
        # TODO add success check
        success = False
        try:
            page_header_text = self.driver.find_element_by_css_selector(CSS_CLASS_HEADER).text
            success = page_header_text == 'LEARN'
        except NoSuchElementException:
            if DEBUG: print('NoSuchElementException')
            success = False
        finally:
            # Save cookies for next time
            if not os.path.exists(COOKIES_FILE):
                with open(COOKIES_FILE, 'w') as f:
                    json.dump(self.driver.get_cookies(), f)
            return success
    def get_current_language(self):
        """ Get current language
        Precondition: Logged in, driver is at URL '/learn'
        Postcondition: self.current_language set to current language on Duo site
        Returns:
            True if successfully set current_language
            False if failed
        """
        if not self.driver.current_url.endswith('/learn'):
            return False

        # Find out which language is currently being learned from dropdown
        lang_name = None
        while lang_name is None:
            lang_icon = self.driver.find_element_by_css_selector(CSS_CLASS_LANG_ICON)
            lang_icon.click()
            try:
                lang_name = self.driver.find_element_by_css_selector(CSS_CLASS_LANG_NAME).text
            except NoSuchElementException:
                if DEBUG: print('NoSuchElementException')
            except StaleElementReferenceException:
                if DEBUG: print('StaleElementReferenceException')
            # Hover over the header to prevent hangups
            try:
                self.driver.find_element_by_css_selector(CSS_CLASS_HEADER).click()
            except ElementNotInteractableException:
                if DEBUG: print('ElementNotInteractableException')

        self.current_language = lang_name
        return True
    def get_skills(self):
        """ Get skills
        Precondition: Logged in, driver is at URL '/learn'
        Postcondition: self.skills set to the list of available skills (list of str)
        Returns:
            True if successfully retrieved skills
            False if failed
        """
        if not self.driver.current_url.endswith('/learn'):
            return False
        skill_elems = self.driver.find_elements_by_css_selector('div[data-test="skill"]')
        self.skills = [s.find_element_by_xpath("./div/div/div[position()=2]").text for s in skill_elems]
        return True
    def start_skill(self, n):
        """ Start skill
        Precondition: Logged in, driver is at URL '/learn', get_skills has been called
        Postcondition: The nth skill button has been clicked and the lesson started.
        Returns:
            True if successful
            False if failed
        """
        if not self.driver.current_url.endswith('/learn') or self.skills is None or len(self.skills) < 1:
            return False
        skill_buttons = self.driver.find_elements_by_css_selector('div[data-test="skill-icon"]')
        # Scroll to the element
        target_y = skill_buttons[n].location['y'] - skill_buttons[0].location['y']
        i = 0
        while i < 5:
            try:
                self.driver.execute_script("javascript:window.scrollBy(0,%d)" % target_y)
                skill_buttons[n].click()
            except ElementClickInterceptedException:
                if DEBUG: print(ElementClickInterceptedException)
            finally:
                i += 1
        start_button = self.driver.find_element_by_css_selector('button[data-test="start-button"]')
        start_button.click()
        return True
    def autocomplete_skill(self, n):
        """ Start skill
        Precondition: Logged in, driver is at URL '/learn', get_skills has been called
        Postcondition: The lesson has been completed. Driver has returned to '/learn'
        Depends on:
            start_skill()
            User input for unknown questions
        Returns:
            True if successful
            False if failed
        """
        if not self.driver.current_url.endswith('/learn') or self.skills is None or len(self.skills) < 1:
            return False

        self.current_lesson = self.skills[n]
        # From dashboard, click buttons to start this skill
        self.start_skill(n)

        old_progress = -1
        progress = 0
        # For each question (including end of lesson)
        while True:
            # Are we completely done this lesson?
            if self.elem_exists(CSS_SELECTOR_LESSON_END):
                print('Done lesson')
                break
            elif self.elem_exists(CSS_SELECTOR_LESSON_START):
                # Just hit next
                pass
            elif self.elem_exists(CSS_SELECTOR_LESSON_MID):
                # Duo is telling us we're doing well
                pass
            elif self.elem_exists('h1[data-test="challenge-header"]'):
                # print('progress: %s' % progress)
                # print('prompt: %s'  % self.driver.find_element_by_css_selector('h1[data-test="challenge-header"] span').text)
                # old_progress = progress
                # progress = self.get_progress()
                # # Answer exactly once for each progress increment
                # if progress == old_progress:
                #     continue
                # else:
                self.answer_question()
            else:
                pass
                print('Warning: unexpected pass')
            # You MUST hit next successfully before continuing
            i = 0
            while not self.press_next() and i < 5:
                i += 1
        # Acknowledge end of lesson
        self.press_next()
        # No thanks to plus
        self.driver.find_element_by_css_selector('button[data-test="no-thanks-to-plus"]').click()
        # Click the skill button again to reset it
        skill_elems = self.driver.find_elements_by_css_selector('div[data-test="skill"]')
        skill_buttons = [s.find_element_by_xpath('./div/div/div[position()=1]') for s in skill_elems]
        skill_buttons[n].click()
        self.current_lesson = None
    def elem_exists(self, css_selector, wait=False):
        # Do not wait the full time for the following find ONLY
        if not wait:
            self.driver.implicitly_wait(0)
        # Perform lookup
        elem_list = self.driver.find_elements_by_css_selector(css_selector)
        # Restore full wait time
        if not wait:
            self.driver.implicitly_wait(self.cfg['webdriver_wait'])
        if len(elem_list) > 0:
            return True
        else:
            return False
    def get_elem(self, css_selector, wait=False):
        if self.elem_exists(css_selector, wait):
            return self.driver.find_element_by_css_selector(css_selector)
        else:
            return None
    def press_next(self):
        # Prevent flameout if we're not actually allowed to click next right now
        if self.is_next_enabled():
            try:
                self.get_next_button().click()
                return True
            except ElementClickInterceptedException:
                if DEBUG: print('ElementClickInterceptedException')
                return False
        return False
    def is_next_enabled(self):
        return CSS_CLASS_NEXT_ENABLED in self.get_next_button().get_attribute('class')
    def get_next_button(self):
        return self.driver.find_element_by_css_selector('button[data-test="player-next"]')
    def answer_question(self):
        """ Answer Question
        Precondition: You're on a question page
        Postcondition: The right answer has been selected / typed
        """
        prompt = self.driver.find_element_by_css_selector('h1[data-test="challenge-header"] span').text
        if prompt == "What sound does this make?":
            q = self.driver.find_element_by_css_selector('span[dir="rtl"]').text
            elem_a = self.driver.find_elements_by_css_selector('div[data-test="challenge-judge-text"]')
            self.complete_multiple_choice(q, elem_a)
        elif prompt.startswith("Select the correct character(s) for"):
            q = prompt.split()[-1][1:-1] # get the last word, remove quotation marks
            elem_a = self.driver.find_elements_by_css_selector('label[data-test="challenge-choice-card"] div:first-child span[dir="rtl"]')
            self.complete_multiple_choice(q, elem_a)
        elif prompt == "Match the pairs":
            elem_tap = self.driver.find_elements_by_css_selector('button[data-test="challenge-tap-token"]')
            self.complete_tapping(elem_tap)
        elif prompt == "Mark the correct meaning":
            q = self.driver.find_element_by_css_selector('.KRKEd._3xka6').text
            elem_a = self.driver.find_elements_by_css_selector('div[data-test="challenge-judge-text"]')
            self.complete_multiple_choice(q, elem_a)
        elif prompt.startswith("Write this in"):
            q = self.driver.find_element_by_css_selector('span[data-test="hint-sentence"]').text
            self.complete_write_in(q)
        elif prompt == "Tap what you hear" or prompt == "Type what you hear":
            # ain't nobody got time for that
            # Click skip
            self.get_elem('button[data-test="player-skip"]', wait=True).click()
        elif prompt.startswith('Which one of these'): # ex: Which one of these is "chicken"?
            q = prompt.split()[-1][1:-2] # Get the last word, strip begin quote, end quote, and question mark
            elem_a = self.driver.find_elements_by_css_selector('label[data-test="challenge-choice-card"] div span[dir="rtl"]')
            self.complete_multiple_choice(q, elem_a)
        else:
            print("Error - Unknown prompt type: %s" % prompt)
            sys.exit(1)
    def complete_multiple_choice(self, q, elem_a):
        # Check brain to see if we know it
        ans = lookup_answer(self.brain, q)
        if ans == None:
            ans = solicit_user_answer(q, [x.text for x in elem_a])
            add_to_brain(self.brain, q, ans, self.current_language, self.current_lesson)
        # Search for match
        match = False
        for elem in elem_a:
            # Bug fixed: must normalize the element data
            if unicodedata.normalize('NFKD', elem.text) == ans:
                try:
                    elem.click()
                except ElementClickInterceptedException:
                    if DEBUG: print('ElementClickInterceptedException')
                break
        # Submit answer
        self.press_next()
        # TODO check if wrong
    def complete_tapping(self, elem_tap):
        tapped = 0
        for elem1 in elem_tap:
            # Continue if elem is already disabled, we selected enough answers,
            # or element reference expired
            try:
                if elem1.is_enabled() == False or tapped >= len(elem_tap) // 2:
                    continue
            except StaleElementReferenceException:
                if DEBUG: print('StaleElementReferenceException')
                continue
            # Find the right answer
            elem1_ans = lookup_answer(self.brain, elem1.text)
            if elem1_ans is None:
                elem1_ans = solicit_user_answer(elem1.text, [x.text for x in elem_tap])
                add_to_brain(self.brain, elem1.text, elem1_ans, self.current_language, self.current_lesson)
            # Click the current element
            elem1.click()
            # Now go click the right answer
            for elem2 in elem_tap:
                if elem2.text == elem1_ans:
                    elem2.click()
                    tapped += 1
                    break
    def complete_write_in(self, q):
        ans = lookup_answer(self.brain, q)
        btn_difficulty = self.get_elem('button[data-test="player-toggle-keyboard"]', wait=True)
        if ans is not None:
            # If the answer is known, ALWAYS hit "Make Harder" if it exists
            if btn_difficulty is not None and btn_difficulty.text == "MAKE HARDER":
                btn_difficulty.click()
            # Then type in the answer
            elem_txt = self.get_elem('textarea[data-test="challenge-translate-input"]')
            try:
                elem_txt.send_keys(ans)
            except AttributeError:
                if DEBUG: print('AttributeError')
                pass # This is probably the end of the lesson
        else:
            # Click "Make easier" so the user doesn't have to type anything but numbers
            if btn_difficulty is not None and btn_difficulty.text == "MAKE EASIER":
                btn_difficulty.click()
            # We may not have that option if it's asking for native language input
            elem_txt = self.get_elem('textarea[data-test="challenge-translate-input"]')
            if elem_txt is not None:
                ans = ''
                while len(ans) < 1:
                    ans = input("Write the answer: ")
                elem_txt.send_keys(ans)
                add_to_brain(self.brain, q, ans, self.current_language, self.current_lesson)
            else:
                # Select the answer one-by-one
                choices = self.driver.find_elements_by_css_selector('button[data-test="challenge-tap-token"]')
                choices_txt = [x.text for x in choices]
                choices_txt.append('Done')
                current_answer = []
                while len(current_answer) < len(choices_txt):
                    last_ans = solicit_user_answer(q, choices_txt)
                    # Is user done?
                    if last_ans == 'Done':
                        break
                    current_answer.append(last_ans)
                    print("Answer so far: %s" % current_answer)
                    # Click the right one
                    for elem in choices:
                        if elem.text == last_ans:
                            elem.click()
                            break
                final_answer = ' '.join(current_answer)
                add_to_brain(self.brain, q, final_answer, self.current_language, self.current_lesson)
        self.press_next()
    def get_progress(self):
        return self.driver.find_element_by_css_selector('._1TkZD').get_attribute('style').split()[-1][:-1] # Get last style (width), shave off the semicolon
if __name__ == "__main__":
    bot = DuoBot()
    bot.perform_login()
    bot.get_current_language()
    print("Currently learning: %s" % bot.current_language)
    if bot.current_language != "Arabic":
        print("Error: Currently only Arabic is supported.") #TODO
        sys.exit(1)
    bot.get_skills()
    print('The following skills are available:')
    print(bot.skills)
    print('Looping through lessons...')
    for i in range(0,11):
        bot.autocomplete_skill(i)

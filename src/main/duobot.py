#!/usr/bin/env python

URL = "https://www.duolingo.com/"
UPDATE_BRAIN = True
COOKIES_FILE = "tmp/cookies.json"
SLEEP_NEXT_QUESTION = 0.5 # seconds
DEBUG = True
TMP_DIR = 'tmp'

CSS_CLASS_HEADER = '._1KHTi._1OomF'
CSS_CLASS_LANG_ICON = '._3gtu3._1-Eux.iDKFi'
CSS_CLASS_LANG_NAME = '.U_ned'
#CSS_CLASS_NEXT_ENABLED = '_2VaJD'
CSS_SELECTOR_PLAYER_NEXT = '[data-test=player-next]'
CSS_SELECTOR_LESSON_START = 'h2.nyHZG'
CSS_SELECTOR_LESSON_MID = 'div._3bFAF._34-WZ._27r1x._3xka6'
CSS_SELECTOR_LESSON_END = 'h2[data-test="answers-correct"]'
CSS_SELECTOR_CHALLENGE_TAP_TOKEN_CLICKED = '._1VtkU'

import time, sys, csv, unicodedata, os
import yaml
import pdb
import json
from inspect import currentframe, getframeinfo
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException, ElementNotInteractableException

from brain import Brain
from util import get_config

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

class DuoBot:
    def __init__(self, ci=False):
        options = webdriver.firefox.options.Options()
        # if not DEBUG or ci: options.headless = True
        self.driver = webdriver.Firefox(log_path='%s/geckodriver.log' % TMP_DIR, options=options)
        self.cfg = get_config()
        #
        self.driver.implicitly_wait(self.cfg['webdriver_wait'])
        #
        self.logged_in = False
        self.current_language = None
        self.current_lesson = None
        self.skills = None
        #
        self.perform_login()
        #self.get_current_language()
        self.current_language = 'Arabic'
        self.brain = Brain(self.current_language)
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
            #elem = self.driver.find_element_by_xpath("//button[@type='submit' and contains(text(),'Log in')]")
            #elem.click()
            # Hit enter to login
            elem.send_keys(Keys.RETURN)
        # Success: URL is correct
        # TODO add success check
        success = False
        try:
            page_header_text = self.driver.find_element_by_css_selector(CSS_CLASS_HEADER).text
            success = page_header_text == 'LEARN'
        except NoSuchElementException:
            if DEBUG: print('NoSuchElementException on line %d' % getframeinfo(currentframe()).lineno)
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
                if DEBUG: print('NoSuchElementException on line %d' % getframeinfo(currentframe()).lineno)
            except StaleElementReferenceException:
                if DEBUG: print('StaleElementReferenceException on line %d' % getframeinfo(currentframe()).lineno)
            # Hover over the header to prevent hangups
            try:
                self.driver.find_element_by_css_selector(CSS_CLASS_HEADER).click()
            except ElementNotInteractableException:
                if DEBUG: print('ElementNotInteractableException on line %d' % getframeinfo(currentframe()).lineno)

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
        i = 0
        while i < 10:
            try:
                skill_buttons = self.driver.find_elements_by_css_selector('div[data-test="skill-icon"]')
                # Scroll to the element
                target_y = skill_buttons[n].location['y'] - 200 # - skill_buttons[0].location['y']
                self.driver.execute_script("javascript:window.scrollBy(0,%d)" % target_y)
                skill_buttons[n].click()
            except ElementClickInterceptedException:
                if DEBUG: print('ElementClickInterceptedException on line %d' % getframeinfo(currentframe()).lineno)
            finally:
                success = True # TODO catch errors
                try:
                    start_button = self.driver.find_element_by_css_selector('button[data-test="start-button"]')
                    print('Start button text: %s' % start_button.text)
                    start_button.click()
                except NoSuchElementException:
                    if DEBUG: print('NoSuchElementException on line %d' % getframeinfo(currentframe()).lineno)
                    i += 1
                break # Break if successfully clicked start
        return True
    def autocomplete_skill(self, url):
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

        self.driver.get(url)

        self.current_lesson = url.split('/')[-2]

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
                try:
                    self.answer_question()
                except NoSuchElementException:
                    if DEBUG: print('NoSuchElementException on line %d' % getframeinfo(currentframe()).lineno)
            else:
                pass
                print('Warning: unexpected pass')
            # You MUST hit next successfully before continuing
            i = 0
            while not self.press_next() and i < 5:
                i += 1
        # Acknowledge end of lesson, streak, lingots award, etc.
        while self.is_next_enabled() and self.get_elem('button[data-test="no-thanks-to-plus"]') is None:
            self.press_next()
        # No thanks to plus
        try:
            self.driver.find_element_by_css_selector('button[data-test="no-thanks-to-plus"]').click()
        except NoSuchElementException:
            if DEBUG: print('NoSuchElementException on line %d' % getframeinfo(currentframe()).lineno)
        # Click the skill button again to reset it
        #skill_elems = self.driver.find_elements_by_css_selector('div[data-test="skill"]')
        #skill_buttons = [s.find_element_by_xpath('./div/div/div[position()=1]') for s in skill_elems]
        #skill_buttons[n].click()
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
        if DEBUG: print('In press_next')
        # Prevent flameout if we're not actually allowed to click next right now
        if self.is_next_enabled():
            try:
                self.get_next_button().click()
                if DEBUG: print('Clicked next')
                return True
            except ElementClickInterceptedException:
                if DEBUG: print('ElementClickInterceptedException on line %d' % getframeinfo(currentframe()).lineno)
                return False
        return False
    def is_next_enabled(self):
        try:
            return self.get_next_button().is_enabled()
        except NoSuchElementException:
            print('NoSuchElementException on line %d' % getframeinfo(currentframe()).lineno)
            if DEBUG: self.dump_and_die()
            return False
    def get_next_button(self):
        return self.driver.find_element_by_css_selector(CSS_SELECTOR_PLAYER_NEXT)
    def answer_question(self):
        """ Answer Question
        Precondition: You're on a question page
        Postcondition: The right answer has been selected / typed
        """
        prompt = self.driver.find_element_by_css_selector('h1[data-test="challenge-header"] span').text
        if DEBUG: print("Answering question with prompt: %s" % prompt)
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
        elif prompt == "Tap what you hear" or prompt == "Type what you hear" or prompt == "What do you hear?":
            # ain't nobody got time for that
            # Click skip
            btn_skip = self.get_elem('button[data-test="player-skip"]', wait=True)
            while btn_skip is not None:
                try:
                    btn_skip.click()
                except ElementClickInterceptedException:
                    print('ElementClickInterceptedException on line %d' % getframeinfo(currentframe()).lineno)
                    btn_skip = self.get_elem('button[data-test="player-skip"]', wait=True)
                except StaleElementReferenceException:
                    print('ElementStaleReferenceException on line %d' % getframeinfo(currentframe()).lineno)
                    break

        elif prompt.startswith('Which one of these'): # ex: Which one of these is "chicken"?
            q = prompt.split()[-1][1:-2] # Get the last word, strip begin quote, end quote, and question mark
            elem_a = self.driver.find_elements_by_css_selector('label[data-test="challenge-choice-card"] div span[dir="rtl"]')
            self.complete_multiple_choice(q, elem_a)
        else:
            print("Error - Unknown prompt type: %s" % prompt)
            sys.exit(1)
    def complete_multiple_choice(self, q, elem_a):
        # Check brain to see if we know it
        ans = self.brain.lookup_answer(q)
        if ans == None:
            ans = solicit_user_answer(q, [x.text for x in elem_a])
            self.brain.add_entry(q, ans, self.current_language, self.current_lesson)
        # Search for match
        match = False
        for elem in elem_a:
            # Bug fixed: must normalize the element data
            # Another bug: Make sure you don't fail out on StaleElementException
            try:
                elem_text = elem.text
            except StaleElementReferenceException:
                print('StaleElementReferenceException on line %d' % getframeinfo(currentframe()).lineno)
                continue
            if unicodedata.normalize('NFKD', elem_text) == ans:
                match = True
                for i in range(0,5):
                    try:
                        elem.click()
                        match = True
                        break # break inner for
                    except ElementClickInterceptedException:
                        if DEBUG: print('ElementClickInterceptedException on line %d' % getframeinfo(currentframe()).lineno)
                    except StaleElementReferenceException:
                        if DEBUG: print('StaleElementReferenceException on line %d' % getframeinfo(currentframe()).lineno)
                break # break outer for
        if match == False:
            print('Warning: match not found')
        # Submit answer
        self.press_next()
        # TODO check if wrong
    def complete_tapping(self, elem_tap):
        # If anything is already tapped by accident, untap it
        tapped_elem = self.get_elem(CSS_SELECTOR_CHALLENGE_TAP_TOKEN_CLICKED)
        if tapped_elem:
            tapped_elem.click()
        tapped = 0
        for elem1 in elem_tap:
            # Continue if elem is already disabled, we selected enough answers,
            # or element reference expired
            try:
                if elem1.is_enabled() == False or tapped >= len(elem_tap) // 2:
                    continue
            except StaleElementReferenceException:
                if DEBUG: print('StaleElementReferenceException on line %d' % getframeinfo(currentframe()).lineno)
                continue
            # Find the right answer
            elem1_ans = self.brain.lookup_answer(elem1.text)
            if elem1_ans is None and elem1.text is not None:
                tapperoo = elem1.text
                try:
                    elem1_ans = solicit_user_answer(elem1.text, [x.text for x in elem_tap])
                except StaleElementReferenceException:
                    print('StaleElementReferenceException on line %d' % getframeinfo(currentframe()).lineno)
                self.brain.add_entry(tapperoo, elem1_ans, self.current_language, self.current_lesson)
            # Click the current element
            elem1.click()
            # Now go click the right answer
            for elem2 in elem_tap:
                try:
                    if elem2.text == elem1_ans:
                        elem2.click()
                        tapped += 1
                        break
                except StaleElementReferenceException:
                    print('StaleElementReferenceException on line %d' % getframeinfo(currentframe()).lineno)
    def complete_write_in(self, q):
        ans = self.brain.lookup_answer(q)
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
                if DEBUG: print('AttributeError on line %d' % getframeinfo(currentframe()).lineno)
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
                self.brain.add_entry(q, ans, self.current_language, self.current_lesson)
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
                self.brain.add_entry(q, final_answer, self.current_language, self.current_lesson)
        self.press_next()
    def get_progress(self):
        return self.driver.find_element_by_css_selector('._1TkZD').get_attribute('style').split()[-1][:-1] # Get last style (width), shave off the semicolon
    def dump_and_die(self):
        print('dumping body HTML')
        html = self.driver.execute_script("return document.body.innerHTML;")
        print(html)
        sys.exit(1)
if __name__ == "__main__":
    if '-ci' in sys.argv:
        print('Running CI-flavored DuoBot session...')
        bot = DuoBot(ci=True)
        bot.autocomplete_skill('https://www.duolingo.com/skill/ar/Alphabet1/practice')
        print('Bot complete.')
    else:
        #TODO fix to use URLS
        print('warning - i am lazy and broke this part. CI is the stuff you need')
        print('DuoBot')
        print('------')
        print('You\'ll be asked to enter a lesson range.')
        print('Examples:')
        print('0')
        print('1-3')
        print('2,4-6,9')
        while True:
            try:
                u_range = input('Please enter lesson range: ')
                ranges = u_range.split(',')
                ranges_filtered = []
                for r in ranges:
                    if '-' in r:
                        start = int(r.split('-')[0])
                        finish = int(r.split('-')[1])
                        ranges_filtered.extend(list(range(start,finish + 1))) # +1 because range is exclusive for the end point
                    else:
                        ranges_filtered.append(int(r))
                break
            except ValueError:
                pass # print('Wrong format. Please try again.')
        print('Selected lessons: %s' % ranges_filtered)
        bot = DuoBot()
        print("Currently learning: %s" % bot.current_language)
        bot.get_skills()
        print('The following skills are available:')
        print(bot.skills)
        print('Looping through lessons...')
        for i in ranges_filtered:
            bot.autocomplete_skill(i)

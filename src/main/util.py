import os
import yaml
from enum import IntEnum

CONFIG_FILE = "config/config.yml"

CSS_LESSON_START = 'h2.nyHZG'
CSS_LESSON_MID = 'div._3bFAF._34-WZ._27r1x._3xka6' # does not work
CSS_LESSON_END = 'h2[data-test="answers-correct"]'
CSS_LESSON_PLUS = '[data-test="plus-continue"]'
CSS_QUESTION = 'h1[data-test="challenge-header"] span'
CSS_QUESTION_SOUND = 'span[dir="rtl"]'
CSS_QUESTION_MARK_MEANING = '.KRKEd._3xka6'
CSS_QUESTION_WRITE_IN = 'span[data-test="hint-sentence"]'
CSS_ANSWER_SOUND = 'div[data-test="challenge-judge-text"]'
CSS_ANSWER_SELECT_CHARACTERS = 'label[data-test="challenge-choice-card"] div:first-child span[dir="rtl"]'
CSS_ANSWER_MATCH_PAIRS = 'button[data-test="challenge-tap-token"]'
CSS_ANSWER_MARK_MEANING = 'div[data-test="challenge-judge-text"]'
CSS_ANSWER_WHICH_ONE = 'label[data-test="challenge-choice-card"] div span[dir="rtl"]'
CSS_NEXT = '[data-test=player-next]'
CSS_SKIP = '[data-test=player-skip]'

cfg = None

class LessonState(IntEnum):
    UNKNOWN = -1
    LESSON_START = 0
    LESSON_END = 1
    LESSON_MID = 2 # duo is saying we're doing well
    LESSON_QUESTION = 3
    LESSON_PLUS = 4 # want to sign up for plus?????

class QuestionState(IntEnum):
    UNKNOWN = -1
    SELECT_SOUND = 0
    SELECT_CHARACTERS = 1
    MATCH_PAIRS = 2
    MARK_MEANING = 3
    WRITE_IN = 4
    LISTENING = 5
    WHICH_ONE = 6
    ANSWER_CORRECT = 7

def get_config():
    global cfg
    if cfg is None:
        # Load username and password from config file
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as ymlfile:
                cfg = yaml.safe_load(ymlfile)
        else:
            cfg = {}
        # Load user/pass from environment if not already there
        if 'username' not in cfg:
            print('Grabbing username from environment var DUO_USERNAME...')
            cfg['username'] = os.environ.get('DUO_USERNAME')
            print('Retrieved value: %s'  % cfg['username'])
        if 'password' not in cfg:
            print('Grabbing password from environment var DUO_PASSWORD...')
            cfg['password'] = os.environ.get('DUO_PASSWORD')
        if 'webdriver_wait' not in cfg:
            print('Adding default value for webdriver_wait')
            cfg['webdriver_wait'] = 5
    return cfg

def elem_exists(driver, css_selector, wait=False):
    # Do not wait the full time for the following find ONLY
    if not wait:
        driver.implicitly_wait(0)
    # Perform lookup
    elem_list = driver.find_elements_by_css_selector(css_selector)
    # Restore full wait time
    if not wait:
        driver.implicitly_wait(get_config()['webdriver_wait'])
    if len(elem_list) > 0:
        return True
    else:
        return False

def get_elem(driver, css_selector, wait=False):
    if elem_exists(driver, css_selector, wait):
        return driver.find_element_by_css_selector(css_selector)
    else:
        return None

def get_lesson_state(driver):
    if elem_exists(driver, CSS_LESSON_START):
        return LessonState.LESSON_START
    elif elem_exists(driver, CSS_LESSON_MID):
        return LessonState.LESSON_MID
    elif elem_exists(driver, CSS_LESSON_END):
        return LessonState.LESSON_END
    elif elem_exists(driver, CSS_QUESTION):
        return LessonState.LESSON_QUESTION
    elif elem_exists(driver, CSS_LESSON_PLUS):
        return LessonState.LESSON_PLUS
    else:
        return LessonState.UNKNOWN

def get_question_state(driver):
    if driver.find_element_by_css_selector(CSS_NEXT).text == 'Continue':
        return QuestionState.ANSWER_CORRECT
    else:
        prompt = driver.find_element_by_css_selector(CSS_QUESTION).text
        if prompt == "What sound does this make?":
            return QuestionState.SELECT_SOUND
        elif prompt.startswith("Select the correct character(s) for"):
            return QuestionState.SELECT_CHARACTERS
        elif prompt == "Match the pairs":
            return QuestionState.MATCH_PAIRS
        elif prompt == "Mark the correct meaning":
            return QuestionState.MARK_MEANING
        elif prompt.startswith("Write this in"):
            return QuestionState.WRITE_IN
        elif prompt == "Tap what you hear" or prompt == "Type what you hear" or prompt == "What do you hear?":
            return QuestionState.LISTENING
        elif prompt.startswith('Which one of these'): # ex: Which one of these is "chicken"?
            return QuestionState.WHICH_ONE
        else:
            return QuestionState.UNKNOWN

def get_question(driver, question_state):
    if question_state == QuestionState.SELECT_SOUND:
        return driver.find_element_by_css_selector(CSS_QUESTION_SOUND).text
    elif question_state == QuestionState.SELECT_CHARACTERS:
        prompt = driver.find_element_by_css_selector(CSS_QUESTION).text
        return prompt.split()[-1][1:-1]
    elif question_state == QuestionState.MATCH_PAIRS:
        return None
    elif question_state == QuestionState.MARK_MEANING:
        return driver.find_element_by_css_selector(CSS_QUESTION_MARK_MEANING).text
    elif question_state == QuestionState.WRITE_IN:
        return driver.find_element_by_css_selector(CSS_QUESTION_WRITE_IN).text
    elif question_state == QuestionState.LISTENING:
        return None # don't care
    elif question_state == QuestionState.WHICH_ONE:
        prompt = driver.find_element_by_css_selector(CSS_QUESTION).text
        return prompt.split()[-1][1:-2]
    else:
        return None

def get_answers(driver, question_state):
    elems = get_answer_elems(driver, question_state)
    if elems is not None:
        return [e.text for e in elems]
    else:
        return None

def get_answer_elems(driver, question_state):
    if question_state == QuestionState.SELECT_SOUND:
        return driver.find_elements_by_css_selector(CSS_ANSWER_SOUND)
    elif question_state == QuestionState.SELECT_CHARACTERS:
        return driver.find_elements_by_css_selector(CSS_ANSWER_SELECT_CHARACTERS)
    elif question_state == QuestionState.MATCH_PAIRS:
        return driver.find_elements_by_css_selector(CSS_ANSWER_MATCH_PAIRS)
    elif question_state == QuestionState.MARK_MEANING:
        return driver.find_elements_by_css_selector(CSS_ANSWER_MARK_MEANING)
    elif question_state == QuestionState.WRITE_IN:
        return None
    elif question_state == QuestionState.LISTENING:
        return None
    elif question_state == QuestionState.WHICH_ONE:
        return driver.find_elements_by_css_selector(CSS_ANSWER_WHICH_ONE)
    else:
        return None

def click_answer(driver, question_state, answer):
    if question_state == QuestionState.SELECT_SOUND or question_state == QuestionState.SELECT_CHARACTERS or question_state == QuestionState.MATCH_PAIRS:
        for e in get_answer_elems(driver, question_state):
            if e.text == answer:
                e.click()
                return True
        return False
    else:
        return False

def click_next(driver):
    try:
        driver.find_element_by_css_selector(CSS_NEXT).click()
        return True
    except:
        return False

def click_skip(driver):
    driver.find_element_by_css_selector(CSS_SKIP).click()
    return True

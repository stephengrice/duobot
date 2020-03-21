import datetime
import unicodedata
import os

DEBUG = False

BRAIN_DIR = "brain"
BRAIN_DELIMITER='|'

class Brain:
    def __init__(self, language):
        self.data = []
        self.language = language
        brain_file = '%s/%s.csv' % (BRAIN_DIR, self.language)
        with open(brain_file) as bf:
            for line in bf:
                data = line.rstrip().split(BRAIN_DELIMITER)
                # Unicodedata normalize NFKD: Map logically equiv chars (such as arabic inital, middle, and end forms, capital letters, japanese kana, etc.)
                self.add_entry(data[0], data[1], data[2], data[3], False)
    def lookup_answer(self, question):
        # Perform unicode normalization
        question = unicodedata.normalize('NFKD', question)
        ans = None
        for line in self.data:
            if line['p1'] == question:
                ans = line['p2']
            elif line['p2'] == question:
                ans = line['p1']
        return ans
    def save_to_file(self):
        # TODO only append new stuff. Check if exists already before append to file
        print('Saving brain file.')
        # Save off the existing file, just in case
        d = datetime.datetime.today()
        timestamp = d.strftime("%Y%m%d_%H%M%S")
        newname = "%s/%s-%s.bak.csv" % (BRAIN_DIR, self.language, timestamp)
        os.rename('%s/%s.csv' % (BRAIN_DIR, self.language), newname)
        print('Existing brain backed up to: %s' % newname)
        # Output the contents of the in-memory brain to csv
        brainfile = '%s/%s.csv' % (BRAIN_DIR, self.language)
        with open(brainfile, 'w') as bf:
            for line in self.data:
                bf.write("%s%s%s%s%s%s%s\n" % (line['p1'], BRAIN_DELIMITER, line['p2'], BRAIN_DELIMITER, line['language'], BRAIN_DELIMITER, line['lesson']))
    def add_entry(self, phrase1, phrase2, language, lesson, save_to_file=True):
        if DEBUG: print("Adding to brain: %s,%s,%s,%s" % (phrase1, phrase2, language, lesson))
        self.data.append({
            'p1' : unicodedata.normalize('NFKD',phrase1),
            'p2' : unicodedata.normalize('NFKD',phrase2),
            'language' : language,
            'lesson': lesson
        })
        if save_to_file:
            self.save_to_file()

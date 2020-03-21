
BRAIN_DIR = "brain"

class Brain:
    def __init__(self, language):
        self.data = []
        self.language = language
        brain_file = '%s/%s.csv' % (BRAIN_DIR, self.language)
        with open(brain_file) as bf:
            for line in bf:
                data = line.rstrip().split(BRAIN_DELIMITER)
                # Unicodedata normalize NFKD: Map logically equiv chars (such as arabic inital, middle, and end forms, capital letters, japanese kana, etc.)
                add_to_brain(brain, data[0], data[1], data[2], data[3], False)

def load_config():
    # Load username and password from config file
    with open(CONFIG_FILE, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    return cfg

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
            brainfile.write("%s%s%s%s%s%s%s\n" % (line['p1'], BRAIN_DELIMITER, line['p2'], BRAIN_DELIMITER, line['language'], BRAIN_DELIMITER, line['lesson']))
def add_to_brain(brain, phrase1, phrase2, language, lesson, update_brain_check=UPDATE_BRAIN):
    # print("Adding to brain: %s,%s,%s,%s" % (phrase1, phrase2, language, lesson))
    brain.append({'p1':unicodedata.normalize('NFKD',phrase1),'p2':unicodedata.normalize('NFKD',phrase2), 'language':language, 'lesson': lesson})
    if update_brain_check:
        update_brain(brain)

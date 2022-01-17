from selenium import webdriver

def main():
    print("Duobot!")
    options = webdriver.firefox.options.Options()
    # if not DEBUG or ci: options.headless = True
    driver = webdriver.Firefox(log_path='geckodriver.log', options=options)
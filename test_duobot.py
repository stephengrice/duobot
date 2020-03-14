from duobot import DuoBot
import unittest

class TestDuoBot(unittest.TestCase):
    def test_perform_login_valid(self):
        bot = DuoBot()
        self.assertTrue(bot.perform_login())
        bot.quit()
    def test_perform_login_invalid(self):
        bot = DuoBot()
        bot.cfg['password'] = 'wrong password'
        self.assertFalse(bot.perform_login())
        bot.quit()

if __name__ == '__main__':
    unittest.main()

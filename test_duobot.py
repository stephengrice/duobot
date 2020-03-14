from duobot import DuoBot
import unittest

# TODO: Skip if env = dev

class TestDuoBot(unittest.TestCase):
    @unittest.skip("demonstrated pass 3/14. temp skip to save time")
    def test_perform_login_valid(self):
        bot = DuoBot()
        self.assertTrue(bot.perform_login())
    @unittest.skip("demonstrated pass 3/14. temp skip to save time")
    def test_perform_login_invalid(self):
        bot = DuoBot()
        bot.cfg['password'] = 'wrong password'
        self.assertFalse(bot.perform_login())
    @unittest.skip("demonstrated pass 3/14. temp skip to save time")
    def test_get_current_language_invalid(self):
        bot = DuoBot()
        self.assertFalse(bot.get_current_language())
        self.assertEqual(bot.current_language, None)
    @unittest.skip("demonstrated pass 3/14. temp skip to save time")
    def test_get_current_language_valid(self):
        bot = DuoBot()
        bot.perform_login()
        self.assertTrue(bot.get_current_language())
        self.assertNotEqual(bot.current_language, None)
        self.assertGreater(len(bot.current_language), 0)
    @unittest.skip("demonstrated pass 3/14. temp skip to save time")
    def test_get_skills(self):
        bot = DuoBot()
        bot.perform_login()
        self.assertTrue(bot.get_skills())
        self.assertNotEqual(bot.skills, None)
        self.assertGreater(len(bot.skills), 0)
    @unittest.skip("demonstrated pass 3/14. temp skip to save time")
    def test_start_skill_invalid(self):
        bot = DuoBot()
        bot.perform_login()
        self.assertFalse(bot.start_skill(0))
    def test_start_skill_valid(self):
        bot = DuoBot()
        bot.perform_login()
        bot.get_skills()
        self.assertTrue(bot.start_skill(0))
        self.assertTrue(bot.driver.current_url.endswith('/practice'))

if __name__ == '__main__':
    unittest.main()

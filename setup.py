from distutils.core import setup

setup(
    name='duobot',
    version='1.0',
    description='Duobot Streak Automator',
    author='Steve Grice',
    author_email='stephengrice@live.com',
    packages=['duobot'],
    entry_points={
        'console_scripts': ['duobot=duobot.cli:main'],
    }
)

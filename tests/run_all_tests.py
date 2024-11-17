import unittest
import os

loader = unittest.TestLoader()
tests = loader.discover(os.path.dirname(__file__))
testRunner = unittest.runner.TextTestRunner()
testRunner.run(tests)
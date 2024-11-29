import unittest
import blendersynth as bsyn

loader = unittest.TestLoader()

# Some tests run in native Python.
if not bsyn.is_blender_running():
    from test_run_this_script import UnitTestRunThisScript
    tests = [UnitTestRunThisScript]

    for test in tests:
        unittest.TextTestRunner().run(loader.loadTestsFromTestCase(test))

# Some tests run in Blender Python.
bsyn.run_this_script()

from test_compositor import UnitTestCompositor
tests = [UnitTestCompositor]
for test in tests:
    unittest.TextTestRunner().run(loader.loadTestsFromTestCase(test))
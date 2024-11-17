"""Unit tests for the run_this_script module."""

import blendersynth as bsyn
import unittest
import os.path
import numpy as np
import subprocess
import tempfile
import sys

resource_folder = os.path.join(os.path.dirname(__file__), "..", "examples", "resources")

def _run_script(text: str, **kwargs) -> (str, str):
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        with open(f.name, "w") as f:
            f.write(text)
        fpath = f.name

        command = [sys.executable, fpath]
        for key, value in kwargs.items():
            command += [f"--{key}", str(value)]

        output = subprocess.run(command, capture_output=True, text=True)

        return output.stdout, output.stderr


class UnitTestRunThisScript(unittest.TestCase):
    def test_kwargs_passed_through(self):

        test_arg_val = 10
        script = f"""
import blendersynth as bsyn
import sys
        
bsyn.run_this_script(test_arg={test_arg_val})
        
print(sys.argv)
        """

        stdout, stderr = _run_script(script)

        argv = eval(stdout.split("\n")[0])
        self.assertIn('--test_arg', argv)
        self.assertEqual(argv[argv.index('--test_arg') + 1], str(test_arg_val))

    def test_argparse_handling(self):

        test_arg = 10
        script = """
import blendersynth as bsyn

parser = bsyn.ArgumentParser()
parser.add_argument("--test_arg", type=int)
parser.add_argument("--test_arg2", type=int, default=5)

args = parser.parse_args()
bsyn.run_this_script(**vars(args))

print(args.test_arg)
print(args.test_arg2)
"""

        stdout, stderr = _run_script(script, test_arg=test_arg)

        lines = stdout.split("\n")
        self.assertEqual(lines[0], str(test_arg))
        self.assertEqual(lines[1], "5")

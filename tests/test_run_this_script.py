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
        
print("SYS:", sys.argv)
        """

        stdout, stderr = _run_script(script)

        sys_line = ""
        for line in stdout.split("\n"):
            if line.startswith("SYS:"):
                sys_line = line
                break

        self.assertNotEqual(sys_line, "")

        sys_argv = eval(sys_line.split("SYS: ")[1])
        self.assertIn("--test_arg", sys_argv)
        self.assertEqual(sys_argv[sys_argv.index('--test_arg') + 1], str(test_arg_val))

    def test_argparse_handling(self):

        test_arg = 10
        script = """
import blendersynth as bsyn

parser = bsyn.ArgumentParser()
parser.add_argument("--test_arg", type=int)
parser.add_argument("--test_arg2", type=int, default=5)

args = parser.parse_args()
bsyn.run_this_script(**vars(args))

print("test_arg", args.test_arg)
print("test_arg2", args.test_arg2)
"""

        stdout, stderr = _run_script(script, test_arg=test_arg)

        lines = stdout.split("\n")
        self.assertIn(f"test_arg {test_arg}", lines)
        self.assertIn("test_arg2 5", lines)

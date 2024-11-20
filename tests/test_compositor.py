
import blendersynth as bsyn
import unittest
import os.path
import numpy as np
import subprocess
import tempfile
import sys

class UnitTestCompositor(unittest.TestCase):

    def test_kwargs_passed_through(self):

        mesh = bsyn.Mesh.from_primitive('cube')
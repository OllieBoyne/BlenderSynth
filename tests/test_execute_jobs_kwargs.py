"""Unit tests verifying that script_kwargs and thread_kwargs are forwarded
correctly through the execute_jobs -> Runner -> BlenderThreadManager ->
BlenderThread chain.

Strategy: test the two components that actually receive the kwargs directly,
rather than mocking six layers to go through execute_jobs end-to-end.

 - BlenderCommand.compose  receives script_kwargs  (turned into CLI flags)
 - BlenderThreadManager    receives thread_kwargs   (forwarded to each BlenderThread)

Only stdlib is used (unittest + tempfile).
"""

import os
import sys
import types
import tempfile
import unittest

# ---------------------------------------------------------------------------
# Bootstrap: blendersynth/__init__.py has heavy side-effects (pip installs,
# Blender-path lookups, ffmpeg imports...). We bypass it by registering
# lightweight stub packages in sys.modules so that the relative imports
# inside run.py and blender_threading.py resolve without executing the
# real __init__.py files.
# ---------------------------------------------------------------------------

if "blendersynth.run.run" not in sys.modules:
    _bs_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), os.pardir, "blendersynth")
    )

    def _make_pkg(name, path):
        mod = types.ModuleType(name)
        mod.__path__ = [path]
        mod.__package__ = name
        sys.modules[name] = mod

    _make_pkg("blendersynth", _bs_root)
    _make_pkg("blendersynth.run", os.path.join(_bs_root, "run"))
    _make_pkg("blendersynth.utils", os.path.join(_bs_root, "utils"))
    _make_pkg("blendersynth.utils.blender_setup",
              os.path.join(_bs_root, "utils", "blender_setup"))
    _make_pkg("blendersynth.file", os.path.join(_bs_root, "file"))

    # Leaf modules imported by run.py that are irrelevant for these tests.
    _tempfiles = types.ModuleType("blendersynth.file.tempfiles")
    _tempfiles.cleanup_temp_files = lambda: None
    sys.modules["blendersynth.file.tempfiles"] = _tempfiles

    _locator = types.ModuleType("blendersynth.utils.blender_setup.blender_locator")
    _locator.get_blender_path = lambda: "/usr/bin/blender"
    sys.modules["blendersynth.utils.blender_setup.blender_locator"] = _locator

# ---------------------------------------------------------------------------

from blendersynth.run.run import BlenderCommand  # noqa: E402
from blendersynth.run.blender_threading import BlenderThreadManager  # noqa: E402


class TestScriptKwargsForwarding(unittest.TestCase):
    """BlenderCommand.compose turns kwargs into ``--key value`` CLI flags."""

    def test_single_kwarg(self):
        cmd = BlenderCommand("blender", background=True)
        cmd.compose(script="s.py", my_arg="hello")

        cli = cmd.command
        self.assertEqual(cli[cli.index("--my_arg") + 1], "hello")

    def test_multiple_kwargs(self):
        cmd = BlenderCommand("blender", background=True)
        cmd.compose(script="s.py", foo="bar", num=42)

        cli = cmd.command
        self.assertEqual(cli[cli.index("--foo") + 1], "bar")
        self.assertEqual(cli[cli.index("--num") + 1], "42")

    def test_no_kwargs(self):
        cmd = BlenderCommand("blender", background=True)
        cmd.compose(script="s.py")

        # Only the structural flags should be present, no stray ``--`` entries
        # beyond the separator that compose always adds.
        after_separator = cmd.command[cmd.command.index("--") + 1:]
        self.assertEqual(after_separator, [])


class TestThreadKwargsForwarding(unittest.TestCase):
    """BlenderThreadManager forwards thread_kwargs to every BlenderThread."""

    def _make_manager(self, tmpdir, jsons, **kwargs):
        cmd = BlenderCommand("blender", background=True)
        cmd.compose(script="s.py")
        mgr = BlenderThreadManager(cmd, jsons, output_directory=tmpdir, **kwargs)
        # Register cleanup so open log file handles don't prevent temp-dir removal.
        for t in mgr.threads:
            if t.logfile is not None:
                self.addCleanup(t.logfile.close)
        return mgr

    def test_timeout_override(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = self._make_manager(d, [["a.json"]], thread_kwargs={"timeout": 500})
            self.assertEqual(mgr.threads[0].timeout, 500)

    def test_default_timeout_without_thread_kwargs(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = self._make_manager(d, [["a.json"]])
            self.assertEqual(mgr.threads[0].timeout, 100)

    def test_none_thread_kwargs_same_as_omitted(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = self._make_manager(d, [["a.json"]], thread_kwargs=None)
            self.assertEqual(mgr.threads[0].timeout, 100)

    def test_all_threads_receive_kwargs(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = self._make_manager(
                d,
                [["a.json"], ["b.json"], ["c.json"]],
                thread_kwargs={"timeout": 250},
            )
            self.assertEqual(len(mgr.threads), 3)
            for thread in mgr.threads:
                self.assertEqual(thread.timeout, 250)

    def test_max_per_job_override(self):
        """thread_kwargs can override values that BlenderThreadManager also
        passes explicitly (e.g. MAX_PER_JOB) without causing a
        'multiple values for keyword argument' error."""
        with tempfile.TemporaryDirectory() as d:
            mgr = self._make_manager(
                d, [["a.json"]], thread_kwargs={"MAX_PER_JOB": 7}
            )
            # BlenderThread splits its jobs list into ceil(n/MAX_PER_JOB)
            # chunks.  With 1 job and MAX_PER_JOB=7 we still get 1 chunk,
            # but the important thing is it didn't crash.
            self.assertEqual(mgr.threads[0].njobs, 1)


if __name__ == "__main__":
    unittest.main()

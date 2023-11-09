import sys
from tqdm import tqdm
from time import perf_counter, sleep
import numpy as np
from subprocess import Popen
import atexit

from datetime import datetime, timedelta
import os


def _list_split(list, chunks):
    """Split a list into chunks"""
    return [[*x] for x in np.array_split(list, chunks)]


class BlenderThread:
    """Manages a list of jobs, which it feeds into sequential Blender instances in a single thread."""

    def __init__(
        self,
        command,
        jobs,
        log_loc,
        progress_loc,
        name="",
        timeout: int = 100,
        to_stdout: bool = False,
        MAX_PER_JOB: int = 100,
        script_directory: str = None,
    ):
        """
        :param progress_loc: .log file to write progress to
        :param timeout: longest time in (s) without render after which process is finished/failed.
        :param to_stdout: If True, print to stdout instead of to a log file.
        :param MAX_PER_JOB: Split command into jobs of size MAX_PER_JOB, and run each job in a separate process.
        :param script_directory: If given, add this to `sys.path` before running the script.
        """

        self.command = command
        self.jobs = _list_split(
            jobs, np.ceil(len(jobs) / MAX_PER_JOB)
        )  # split jobs into chunks of MAX_PER_JOB
        self.njobs = len(self.jobs)

        self.size = len(jobs)
        self.timeout = timeout
        self.script_directory = script_directory

        self.prev_n = (
            0  # store how many rendered to check for updates for timeout purposes
        )
        self.timer = perf_counter()

        self.to_stdout = to_stdout
        if not self.to_stdout and log_loc is not None:
            self.log_loc = log_loc
            self.logfile = open(self.log_loc, "a")
        else:
            self.log_loc, self.logfile = None, None

        self.logger_loc = progress_loc

        self.process = None
        self.job = -1
        self.finished = False

        self.name = name
        self.status = f"STARTED THREAD {self.name}"

    def check_in(self):
        """Checks if current job still running, if not move to next job.
        If all jobs complete, set self.finished = True"""
        if self.is_running:
            return

        self.job += 1

        if self.job >= self.njobs:
            self.finished = True
            self.status = f"✓ THREAD {self.name} COMPLETED."
            return

        self.status = f"THREAD {self.name} RUNNING JOB {self.job + 1}/{self.njobs}..."
        self.start_job(self.job)

    def start_job(self, job: int = 0):
        """
        :param job: Index of job to start
        """
        job_list = self.jobs[job]
        command = self.command.set_job(job_list).set_logger(self.logger_loc).command

        stdout = sys.stdout if self.to_stdout else self.logfile
        stderr = sys.stderr if self.to_stdout else self.logfile

        env = os.environ.copy()
        if self.script_directory is not None:
            env["PYTHONPATH"] = (
                self.script_directory + os.pathsep + env.get("PYTHONPATH", "")
            )

        self.process = Popen(
            command, universal_newlines=True, stdout=stdout, stderr=stderr, env=env
        )

    def terminate(self):
        """End process"""
        self.process.kill()

    def kill(self):
        self.terminate()

    @property
    def is_running(self):
        if self.process:
            return self.process.poll() is None
        return False

    @property
    def complete(self):
        if not self.is_running:
            self.logfile.flush()
            return True

    def __len__(self):
        return self.size

    @property
    def num_rendered(self):
        """Read through Log file to find how many renders have been completed"""
        if self.process is None or not os.path.isfile(self.logger_loc):
            return 0  # process not started yet

        x = 0
        with open(self.logger_loc, "r") as f:
            for line in f.readlines():
                x += 1  # currently only 1 type of message to logger - render complete

        return x

    def remaining_idxs(self):
        raise NotImplementedError()

    @property
    def success(self):
        return self.num_rendered == self.size

    def check_status(self):
        """True if still running successfully, False if exceeded timeout"""
        n = self.num_rendered
        if n > self.prev_n:
            self.prev_n = n
            self.timer = perf_counter()

        elif (perf_counter() - self.timer) >= self.timeout:
            self.status = f"✖ THREAD {self.name} FAILED [TIMEOUT]."
            return False

        return True


class BlenderThreadManager:
    """Manager of multiple :class:`~blendersynth.run.blender_threading.BlenderThread` instances"""

    def __init__(
        self,
        command,
        jsons,
        output_directory,
        print_to_stdout=False,
        MAX_PER_JOB=100,
        script_directory=None,
    ):
        """
        :param commands: Base Blender command to run
        :param jsons: A list of num_threads size, each element is a list of jsons to render from
        :param log_locs:
        :param MAX_PER_JOB: To prevent memory issues, split up jobs into chunks of MAX_PER_JOB
        :param script_directory: If given, add this to `sys.path` before running the script.
        """
        self.num_threads = len(jsons)

        self.command = command

        # create logs
        session_name = datetime.now().strftime(r"%y%m%d-%H%M%S")
        log_dir = os.path.join(output_directory, "logs", session_name)
        progress_dir = os.path.join(log_dir, "_progress")  # for storing progress

        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(progress_dir, exist_ok=True)

        logs = [
            os.path.join(log_dir, f"log_{i:02d}.txt") for i in range(self.num_threads)
        ]
        progresses = [
            os.path.join(progress_dir, f"progress_{i:02d}.log")
            for i in range(self.num_threads)
        ]
        self.log_locs = logs

        # Set report name as report_xx, incrementing by 1 each report
        report_fname = f"report_{len([f for f in os.listdir(output_directory) if 'report' in f]):02d}.txt"
        self.report_loc = os.path.join(output_directory, report_fname)

        self.t0 = 0
        self.session_start = None

        self.threads = []
        for i in range(self.num_threads):
            thread = BlenderThread(
                command,
                jobs=jsons[i],
                log_loc=None if logs is None else logs[i],
                progress_loc=progresses[i],
                name=str(i),
                to_stdout=print_to_stdout,
                MAX_PER_JOB=MAX_PER_JOB,
                script_directory=script_directory,
            )

            self.threads.append(thread)

    def __len__(self):
        return sum(map(len, self.threads))

    def start(
        self,
        progress_bars: bool = True,
        tick: float = 0.5,
        report_every: float = 15.0,
        offset: float = 1.0,
    ):
        """Start all threads and job progress
        :param progress_bars: Show progress bars for each thread and overall progress
        :param tick: How often to update progress bars
        :param report_every: How often to print status updates to log
        :param offset: How long to wait before starting each thread (to avoid memory issues)
        """
        self.t0 = perf_counter()  # log start time
        self.session_start = datetime.now()

        for thread in self.threads:
            thread.check_in()
            sleep(offset)

        # register atexit handler
        atexit.register(self.terminate)

        last_report_time = perf_counter()

        if progress_bars:
            pbars = []
            bar_format = "{l_bar}{bar:10}{r_bar}{bar:-10b}"
            for i, thread in enumerate(self.threads):
                p = tqdm(
                    total=len(thread),
                    initial=thread.num_rendered,
                    bar_format=bar_format,
                    position=i + 1,
                )
                pbars.append(p)

            with tqdm(total=len(self), bar_format=bar_format, position=0) as pbar:
                while any(t.is_running for t in self.threads):
                    sleep(tick)

                    # Update progress bar
                    rendered_images = self.num_rendered

                    desc = "Session rendering..."
                    desc += f" [Dataset: {rendered_images}/{len(self)}]"
                    pbar.set_description(desc)

                    pbar.n = self.num_rendered
                    pbar.refresh()

                    if (perf_counter() - last_report_time) >= report_every:
                        self.update_report()
                        last_report_time = perf_counter()

                    # Update sub-progress bars, restart threads if needed
                    for t, thread in enumerate(self.threads):
                        if thread.finished:
                            continue

                        thread.check_in()

                        if thread.success:
                            pbars[t].n = thread.num_rendered

                        else:
                            thread_running = thread.check_status()

                            if thread_running:
                                pbars[t].n = thread.num_rendered

                            else:  # Thread failed, currently will only notify the user
                                pass

                        pbars[t].set_description(thread.status)

            self.update_report()

    @property
    def num_rendered(self):
        return sum(t.num_rendered for t in self.threads)

    def update_report(self):
        t1 = perf_counter()
        elapsed = t1 - self.t0

        report = []
        if self.num_rendered > 0:
            # calculate number of seconds remaining
            s_remaining = (len(self) - self.num_rendered) * (
                elapsed / self.num_rendered
            )
            eta = datetime.now() + timedelta(seconds=s_remaining)

            report += [
                f"Number of images rendered: {self.num_rendered}\n",
                f"Total session quota: {len(self)}\n",
                f"Time elapsed: {timedelta(seconds=round(elapsed))}\n",
                f"Time per render (s): {elapsed / self.num_rendered:.2f}\n\n",
                f"Session start: {self.session_start.strftime('%I:%M %p %d/%m/%y')}\n"
                f"Estimated End: {eta.strftime('%I:%M %p %d/%m/%y')}",
            ]

        with open(self.report_loc, "w") as outfile:
            outfile.writelines(report)

    def terminate(self):
        """End all threads"""
        for thread in self.threads:
            thread.terminate()

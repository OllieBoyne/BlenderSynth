"""When constructing a dataset, the INPUTS object below will
return an iterable with read's in sys.argv's `--jobs` jsons."""

import sys
import json
import os
import logging
from typing import Union, List


class Inputs:
    """This class is used to iterate over the JSONs passed in via `--jobs` in sys.argv.

    Will also convert all kwargs to attributes for easy access"""

    jsons = None
    """List of JSON files passed in via `--jobs` in sys.argv."""

    def __init__(self):
        self.jsons = sys.argv[sys.argv.index("--jobs") + 1].split(",")
        log_loc = sys.argv[sys.argv.index("--log") + 1]

        # Set up logging
        logging.basicConfig(
            filename=log_loc,
            level=logging.INFO,
            filemode="a",
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

        # store all --kwargs as attributes
        for k, v in zip(sys.argv, sys.argv[1:]):
            if k.startswith("--"):
                setattr(self, k[2:], v)

    def __iter__(self):
        for n, j in enumerate(self.jsons):
            with open(j, "r") as f:
                fname = os.path.splitext(os.path.split(j)[-1])[0]
                yield fname, json.load(f)

            # Once we get here, we've passed 'yield', so we know that JSON has been loaded & rendering has occured
            logging.info(f"RENDERED: {fname}")

    def __len__(self):
        return len(self.jsons)


class DebugInputs(Inputs):
    """Class to emulate the Inputs class, for a single JSON for testing."""

    def __init__(self, json_loc: Union[str, List], repeats: int = 1):
        """

        :param json_loc: Location of JSON(s) to use
        :param repeat: Number of times to repeat the JSON(s)
        """
        if isinstance(json_loc, str):
            json_loc = [json_loc]

        self.jsons = json_loc * repeats

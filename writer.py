#!/usr/bin/env python3

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile, mkstemp


def write_status_safe(status, message, status_file, tempdir=None):
    """
    Atomically write a JSON structure to a file.

    This uses temp files and atomic moves to make sure any client reading the
    file will always have a complete and consistent view of the file. If the
    status file is on a separate mountpoint from the system temp dir, use the
    tempdir arg to specify a temp dir on the same mount as the status file to
    preserve the ability to do atomic filesystem moves.

    Args:
        status:         the current status (str)
        message:        human descriptive message (str)
        status_file:    the file to write (path-like)
        tempdir:        the temporary directory to use (path-like)
    """

    status = {
        "status": status,
        "message" : message
    }

    tmpname = None
    try:
        with NamedTemporaryFile(dir=tempdir, delete=False, mode="w", encoding="utf8") as tmpfile:
            tmpname = tmpfile.name
            json.dump(status, tmpfile, default=str)
        os.replace(tmpfile.name, str(status_file))
    finally:
        try:
            os.remove(tmpname)
        except (TypeError, OSError):
            pass


# The rest is code to test/prove thee atomicity of the file write/read.
# To see the test fail, change the call to write_status_safe to 
# # write_status_unsafe. The read thread will quickly hit an incomplete write
# and read partial JSON from the status file, crashing the thread.

from multiprocessing import Pool
from random import random, choice
import time
import traceback

status_choices = ["running", "error", "success"]
message_choices = ["Doing stuff", "Other stuff", "More stuff"]

def write_status_unsafe(status, message, status_file, tempdir=None):
    """Write a JSON structure to a file non-atomically"""
    with open(status_file, "w") as fh:
        json.dump(status, fh)

def read_status_thread(status_file):
    """Continuously read the status file and test the contents"""
    print("Starting -> read thread")
    last_status = ""
    last_message = ""
    while True:
        try:
            with open(status_file, "r") as fh:
                status = json.load(fh)
        except FileNotFoundError:
            continue
        assert(status["status"] in status_choices)
        assert(status["message"] in message_choices)
        if last_status != status["status"] or last_message != status["message"]:
            print("->    Read content {}: {}".format(status["status"], 
                                                     status["message"]))
            last_status = status["status"]
            last_message = status["message"]

def write_status_thread(status_file):
    """Continuously write new content to the status file"""
    print("Starting <- write thread")
    new_status = last_status = ""
    new_message = last_message = ""
    while True:
        time.sleep(random())
        while new_status == last_status and new_message == last_message:
            new_status = choice(status_choices)
            new_message = choice(message_choices)
        print("<- Writing content {}: {}".format(new_status, new_message))
        write_status_safe(new_status, new_message, status_file)
        # write_status_unsafe(new_status, new_message, status_file)
        last_status = new_status
        last_message = new_message


if __name__ == "__main__":
    cwd = Path(os.getcwd())
    stat_filename = cwd / "status.json"
    try:
        os.remove(stat_filename)
    except FileNotFoundError:
        pass

    results = []
    with Pool(processes=2) as pool:
        results.append(pool.apply_async(read_status_thread, (stat_filename,)))
        results.append(pool.apply_async(write_status_thread, (stat_filename,)))
        for res in results:
            res.get(0xFFFF)

#!/usr/bin/env python

from functools import wraps
import itertools
import sys
import time
import threading


class Spinner:

    def __init__(self):
        self.busy = False
        self.interval = 0.1
        self.frames = itertools.cycle(['-', '/', '|', '\\'])
    
    def spin(self):
        while self.busy:
            sys.stdout.write(next(self.frames))
            sys.stdout.flush()
            time.sleep(self.interval)
            sys.stdout.write('\b')
            sys.stdout.flush()

    def start(self):
        self.busy = True
        threading.Thread(target=self.spin).start()
    
    def stop(self):
        self.busy = False
        time.sleep(self.interval)


def spinner_decorator(initial_msg, done_msg):
    spinner = Spinner()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(initial_msg, end='')
            func(*args, **kwargs)
            print(done_msg)
        
        return wrapper

    return decorator
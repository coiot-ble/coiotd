import logging
import sys

def activate_log(*names):
    for name in names:
        log = logging.getLogger(name)
        log.level = logging.DEBUG
        log.addHandler(logging.StreamHandler(sys.stdout))

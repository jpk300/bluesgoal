#!/usr/bin/python3

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config import RELAY_ACTIVE_LOW, RELAY_PINS

GOALHORN_DIR = Path(__file__).resolve().parents[1]
relay_off_level = True if RELAY_ACTIVE_LOW else False

try:
    import RPi.GPIO as GPIO

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(RELAY_PINS, GPIO.OUT, initial=relay_off_level)
    GPIO.output(RELAY_PINS, relay_off_level)
finally:
    try:
        GPIO.cleanup()
    except Exception:
        pass

subprocess.run(['python3', '-B', str(GOALHORN_DIR / 'stop' / 'stop.py')], check=False)
print('Audio stopped')

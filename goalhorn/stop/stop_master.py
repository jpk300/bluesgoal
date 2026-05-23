#!/usr/bin/python3

import subprocess

try:
    import RPi.GPIO as GPIO

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup([7, 8], GPIO.OUT, initial=GPIO.HIGH)
    GPIO.output([7, 8], GPIO.HIGH)
finally:
    try:
        GPIO.cleanup()
    except Exception:
        pass

subprocess.run(['python3', '/var/www/html/goalhorn/stop/stop.py'], check=False)
print('Audio stopped')

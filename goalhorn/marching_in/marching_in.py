#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import subprocess

GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BOARD)

PINS = [7, 8]

# Active-low relay setup
GPIO.setup(PINS, GPIO.OUT, initial=GPIO.HIGH)

try:
    print("Turning relays ON")
    GPIO.output(PINS, GPIO.LOW)

    print("Stopping old audio if running")
    subprocess.run(["pkill", "-f", "mpg321"], stderr=subprocess.DEVNULL)
    time.sleep(0.25)

    print("Starting audio")
    subprocess.Popen([
        "mpg321",
        "/var/www/html/mp3/marching_in.mp3"
    ])

    print("Keeping relays active for 30 seconds")
    time.sleep(30)

    print("Turning relays OFF")
    GPIO.output(PINS, GPIO.HIGH)

finally:
    GPIO.cleanup()

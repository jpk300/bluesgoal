#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import subprocess

GPIO.setwarnings(False)
GPIO.cleanup()

GPIO.setmode(GPIO.BOARD)

PINS = [7, 8]

# Active LOW relay board
GPIO.setup(PINS, GPIO.OUT, initial=GPIO.HIGH)

try:

    print("Turning relays ON")

    # ON
    GPIO.output(PINS, GPIO.LOW)

    print("Starting audio")

    subprocess.Popen([
        "mpg321",
        "-a",
        "hw:1,0",
        "/var/www/html/mp3/marching_in_glenn.mp3"
    ])

    print("Keeping relays active for 30 seconds")

    time.sleep(30)

    print("Turning relays OFF")

    # OFF
    GPIO.output(PINS, GPIO.HIGH)

except Exception as e:
    print(f"Error: {e}")

finally:

    print("Cleaning up GPIO")

    GPIO.cleanup()

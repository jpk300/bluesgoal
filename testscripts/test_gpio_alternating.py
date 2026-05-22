#!/usr/bin/python3

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

pins = [7, 8]

# Configure all pins as outputs
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

try:
    while True:
        for pin in pins:
            print(f"Testing pin {pin}")

            GPIO.output(pin, GPIO.HIGH)
            time.sleep(2)

            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.5)

except KeyboardInterrupt:
    print("Stopped by user")

finally:
    GPIO.cleanup()

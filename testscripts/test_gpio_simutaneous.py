#!/usr/bin/python3

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

PIN_1 = 7
PIN_2 = 8

GPIO.setup(PIN_1, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(PIN_2, GPIO.OUT, initial=GPIO.LOW)

try:
    while True:
        print("BOTH ON")

        GPIO.output(PIN_1, GPIO.HIGH)
        GPIO.output(PIN_2, GPIO.HIGH)

        time.sleep(2)

        print("BOTH OFF")

        GPIO.output(PIN_1, GPIO.LOW)
        GPIO.output(PIN_2, GPIO.LOW)

        time.sleep(10)

except KeyboardInterrupt:
    print("Stopping test")

finally:
    GPIO.cleanup()

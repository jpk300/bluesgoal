#!/usr/bin/python
import RPi.GPIO as GPIO, time, os, subprocess
GPIO.setmode (GPIO.BOARD)
subprocess.Popen(["python", '/var/www/html/goalhorn/stop/stop.py'])
GPIO.setup(7,GPIO.IN)
GPIO.setup(8,GPIO.IN)
time.sleep(1)
GPIO.cleanup()

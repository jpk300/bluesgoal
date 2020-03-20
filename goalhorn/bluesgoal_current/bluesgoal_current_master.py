#!/usr/bin/python
import RPi.GPIO as GPIO, time, os, subprocess
GPIO.setmode (GPIO.BOARD)
GPIO.setup(7,GPIO.IN)
GPIO.setup(8,GPIO.IN)
subprocess.Popen(["python", '/var/www/html/goalhorn/bluesgoal_current/bluesgoal_current.py'])
time.sleep(1)
GPIO.setup(7,GPIO.OUT)
GPIO.setup(8,GPIO.OUT)
time.sleep(30)
GPIO.setup(7,GPIO.IN)
GPIO.setup(8,GPIO.IN)
time.sleep(1)
GPIO.cleanup()

#!/usr/bin/python
import RPi.GPIO as GPIO, time, os, subprocess
subprocess.Popen(["python", '/var/www/html/goalhorn/volume/volume_75.py'])
time.sleep(1)

#!/usr/bin/python3

import subprocess
import time

subprocess.run(['python3', '/var/www/html/goalhorn/volume/volume_up.py'], check=False)
time.sleep(1)

#!/usr/bin/python3

import subprocess

subprocess.run(['pkill', '-f', 'mpg321'], stderr=subprocess.DEVNULL, check=False)

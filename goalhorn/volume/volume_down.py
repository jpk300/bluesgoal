#!/usr/bin/python3

import subprocess

subprocess.run([
    "amixer",
    "-c",
    "1",
    "set",
    "PCM",
    "5dB-"
])

subprocess.run([
    "amixer",
    "-c",
    "1",
    "get",
    "PCM"
])

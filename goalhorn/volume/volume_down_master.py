#!/usr/bin/python3

import subprocess
import time
from pathlib import Path

GOALHORN_DIR = Path(__file__).resolve().parents[1]

subprocess.run(['python3', str(GOALHORN_DIR / 'volume' / 'volume_down.py')], check=False)
time.sleep(1)

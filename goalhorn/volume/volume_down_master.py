#!/usr/bin/python3

import subprocess
import time
from pathlib import Path

GOALHORN_DIR = Path(__file__).resolve().parents[1]

result = subprocess.run(['python3', '-B', str(GOALHORN_DIR / 'volume' / 'volume_down.py')], check=False)
time.sleep(1)
raise SystemExit(result.returncode)

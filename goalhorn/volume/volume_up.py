#!/usr/bin/python3

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config import AUDIO_CARD, VOLUME_STEP

subprocess.run([
    "amixer",
    "-c",
    str(AUDIO_CARD),
    "set",
    "PCM",
    f"{VOLUME_STEP}+"
])

subprocess.run([
    "amixer",
    "-c",
    str(AUDIO_CARD),
    "get",
    "PCM"
])

#!/usr/bin/python3

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config import AUDIO_CARD, VOLUME_STEP

def run_amixer(args):
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


run_amixer([
    "amixer",
    "-c",
    str(AUDIO_CARD),
    "set",
    "PCM",
    f"{VOLUME_STEP}+",
])

run_amixer([
    "amixer",
    "-c",
    str(AUDIO_CARD),
    "get",
    "PCM",
])

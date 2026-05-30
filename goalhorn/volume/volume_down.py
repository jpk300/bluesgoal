#!/usr/bin/python3

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config import AUDIO_CARD, AUDIO_MIXER_CONTROL, VOLUME_STEP
from goalhorn.volume.alsa_mixer import choose_control, run_amixer as run_amixer_command


def run_amixer(args):
    result = run_amixer_command(args)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

mixer_control, _ = choose_control(AUDIO_CARD, AUDIO_MIXER_CONTROL)

run_amixer([
    "-c",
    str(AUDIO_CARD),
    "set",
    mixer_control,
    f"{VOLUME_STEP}-",
])

run_amixer([
    "-c",
    str(AUDIO_CARD),
    "get",
    mixer_control,
])

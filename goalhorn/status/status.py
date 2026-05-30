#!/usr/bin/python3

"""
Return current audio state and ALSA volume as JSON for the web UI.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config import AUDIO_CARD, AUDIO_MIXER_CONTROL, AUDIO_PLAYER
from goalhorn.volume.alsa_mixer import choose_control


def run_command(args):
    try:
        return subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        return subprocess.CompletedProcess(args, 127, stdout='', stderr=str(error))


def get_volume():
    mixer_control, _ = choose_control(AUDIO_CARD, AUDIO_MIXER_CONTROL)
    result = run_command(['amixer', '-c', str(AUDIO_CARD), 'get', mixer_control])
    if result.returncode != 0:
        return 'unknown'

    match = re.search(r'\[(\d{1,3})%\]', result.stdout)
    if not match:
        return 'unknown'

    return int(match.group(1))


def is_audio_playing():
    player_name = Path(AUDIO_PLAYER).name
    result = run_command(['pgrep', '-x', player_name])
    return result.returncode == 0


def main():
    payload = {
        'success': True,
        'data': {
            'volume': get_volume(),
            'audio_playing': is_audio_playing(),
        },
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    print(json.dumps(payload))


if __name__ == '__main__':
    main()

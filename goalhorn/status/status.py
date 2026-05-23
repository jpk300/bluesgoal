#!/usr/bin/python3

"""
Return current audio state and ALSA volume as JSON for the web UI.
"""

import json
import re
import subprocess
from datetime import datetime


def run_command(args):
    return subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )


def get_volume():
    result = run_command(['amixer', '-c', '1', 'get', 'PCM'])
    if result.returncode != 0:
        return 'unknown'

    match = re.search(r'\[(\d{1,3})%\]', result.stdout)
    if not match:
        return 'unknown'

    return int(match.group(1))


def is_audio_playing():
    result = run_command(['pgrep', '-f', 'mpg321'])
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

#!/usr/bin/python3

"""
Small ALSA helpers for selecting the mixer control used by volume/status.
"""

import re
import subprocess


PREFERRED_CONTROLS = ('PCM', 'Master', 'Headphone', 'Speaker', 'Digital')


def run_amixer(args):
    try:
        return subprocess.run(
            ['amixer', *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:
        return subprocess.CompletedProcess(['amixer', *args], 127, stdout='', stderr=str(error))


def list_controls(audio_card):
    result = run_amixer(['-c', str(audio_card), 'scontrols'])
    if result.returncode != 0:
        return [], result

    controls = re.findall(r"Simple mixer control '([^']+)'", result.stdout)
    return controls, result


def choose_control(audio_card, configured_control=''):
    controls, result = list_controls(audio_card)
    if result.returncode != 0:
        return configured_control or 'PCM', result

    if configured_control:
        return configured_control, result

    for control in PREFERRED_CONTROLS:
        if control in controls:
            return control, result

    return controls[0] if controls else 'PCM', result

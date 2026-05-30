#!/usr/bin/python3
"""Shared GPIO/audio action runner for Blues goal horn sounds."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config import AUDIO_PLAYER, MP3_DIR, RELAY_ACTIVE_LOW, RELAY_DURATION, RELAY_PINS, SOUNDS


def relay_on_level():
    """Return the GPIO level that activates the relay."""
    return False if RELAY_ACTIVE_LOW else True


def relay_off_level():
    """Return the GPIO level that deactivates the relay."""
    return True if RELAY_ACTIVE_LOW else False


def stop_audio():
    """Stop any existing audio player process before starting a new horn."""
    subprocess.run(["pkill", "-f", AUDIO_PLAYER], stderr=subprocess.DEVNULL, check=False)
    time.sleep(0.25)


def setup_gpio():
    """Configure relay pins and return the GPIO module for cleanup/output."""
    import RPi.GPIO as GPIO

    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(RELAY_PINS, GPIO.OUT, initial=relay_off_level())
    return GPIO


def play_audio(mp3_path):
    """Start the configured audio player for the selected MP3 file."""
    return subprocess.Popen([AUDIO_PLAYER, str(mp3_path)])


def run_action(action):
    """Run a validated goal horn action through one shared GPIO/audio lifecycle."""
    if action not in SOUNDS:
        allowed = ", ".join(sorted(SOUNDS))
        raise ValueError(f"Unsupported action '{action}'. Allowed actions: {allowed}")

    mp3_path = Path(MP3_DIR) / SOUNDS[action]
    if not mp3_path.exists():
        raise FileNotFoundError(f"Audio file not found: {mp3_path}")

    stop_audio()

    gpio = setup_gpio()
    try:
        print(f"Turning relays ON for {action}")
        gpio.output(RELAY_PINS, relay_on_level())

        print(f"Starting audio: {mp3_path}")
        play_audio(mp3_path)

        print(f"Keeping relays active for {RELAY_DURATION} seconds")
        time.sleep(RELAY_DURATION)

        print("Turning relays OFF")
        gpio.output(RELAY_PINS, relay_off_level())
    finally:
        try:
            gpio.output(RELAY_PINS, relay_off_level())
        finally:
            gpio.cleanup()

    return {
        "success": True,
        "action": action,
        "audio_file": str(mp3_path),
        "relay_pins": RELAY_PINS,
        "relay_duration_seconds": RELAY_DURATION,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run a Blues goal horn sound action")
    parser.add_argument("action", choices=sorted(SOUNDS), help="Sound action to run")
    args = parser.parse_args(argv)

    try:
        result = run_action(args.action)
    except Exception as error:
        print(json.dumps({
            "success": False,
            "action": args.action,
            "error": str(error),
        }))
        return 1

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

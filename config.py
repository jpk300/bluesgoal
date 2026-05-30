#!/usr/bin/python3

"""
Configuration file for Blues Goal Horn application.
Centralized settings for easy customization.
"""

import os
from pathlib import Path

# ============================================================================
# PATHS
# ============================================================================
BASE_PATH = os.environ.get('BLUESGOAL_BASE_PATH', '/var/www/html')
MP3_DIR = os.environ.get('BLUESGOAL_MP3_DIR', os.path.join(BASE_PATH, 'mp3'))
LOG_DIR = os.environ.get('BLUESGOAL_LOG_DIR', os.path.join(BASE_PATH, 'logs'))
HISTORY_FILE = os.path.join(LOG_DIR, 'history.log')
ERROR_LOG_FILE = os.path.join(LOG_DIR, 'error.log')

# ============================================================================
# GPIO SETTINGS
# ============================================================================
GPIO_MODE = 'BOARD'  # Use BOARD pin numbering
RELAY_PINS = [7, 8]
RELAY_ACTIVE_LOW = True  # True = HIGH is OFF, LOW is ON
RELAY_DURATION = 30  # seconds

# ============================================================================
# AUDIO SETTINGS
# ============================================================================
AUDIO_CARD = os.environ.get('BLUESGOAL_AUDIO_CARD', '1')  # ALSA card number
AUDIO_MIXER_CONTROL = os.environ.get('BLUESGOAL_AUDIO_MIXER_CONTROL', '')  # Empty = auto-detect
VOLUME_STEP = os.environ.get('BLUESGOAL_VOLUME_STEP', '5dB')  # Step size for volume control
AUDIO_PLAYER = os.environ.get('BLUESGOAL_AUDIO_PLAYER', 'mpg321')  # Command to use for audio playback

# ============================================================================
# SOUND CONFIGURATIONS
# ============================================================================
# Map button actions to audio files
SOUNDS = {
    'powerplay': 'powerplay.mp3',
    'bluesgoal_winterclassic': 'bluesgoal_winterclassic.mp3',
    'bluesgoal_oldschool': 'bluesgoal_oldschool.mp3',
    'marching_in': 'marching_in.mp3',
    'marching_in_glenn': 'marching_in_glenn.mp3',
}

# ============================================================================
# BUTTON LABELS FOR UI
# ============================================================================
BUTTON_LABELS = {
    'powerplay': 'Power Play',
    'bluesgoal_winterclassic': 'Winter Classic',
    'bluesgoal_oldschool': 'Old School',
    'marching_in': 'Marching In',
    'marching_in_glenn': 'Marching In (Glenn)',
    'volume_up': 'Volume Up',
    'volume_down': 'Volume Down',
    'stop': 'Stop',
}

# ============================================================================
# LOGGING SETTINGS
# ============================================================================
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ============================================================================
# Helper functions to ensure directories exist
# ============================================================================
def ensure_log_dir():
    """Create log directory if it doesn't exist."""
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    try:
        log_dir.chmod(0o755)
    except PermissionError:
        # Directory ownership is handled by deployment; logging callers will
        # still surface write failures through logger.log_error().
        pass


ensure_log_dir()

# St. Louis Blues Goal Horn Web App

**Last updated:** May 30, 2026
**Current Version:** v2.1.0

A local Raspberry Pi web app for St. Louis Blues goal celebrations. The app provides a touch-friendly Apache/PHP interface that triggers goal horn audio, GPIO-controlled LED strobes, stop and volume controls, activity logging, and optional NHL API goal detection.

> **Deployment assumption:** v2.1.0 still expects the application files to live directly in Apache's default document root: `/var/www/html`. Core Python scripts now support environment overrides for several paths and audio settings, but PHP entrypoints still invoke some `/var/www/html/...` paths, so installing into `/var/www/html/bluesgoal` still requires additional code/config changes or symlinks.

## Overview

This project is a small Python/PHP application intended for a trusted home LAN. PHP endpoints receive button/API requests from the web UI, then invoke Python scripts that control audio playback, Raspberry Pi GPIO pins, volume, logging, and the optional NHL feed worker.

**Primary components:**
- **Python** - Audio, GPIO, status, logging, volume, and NHL worker logic
- **PHP** - Apache-accessible JSON endpoints and action dispatch
- **HTML/CSS/JavaScript** - Main control page and settings page
- **Local assets** - User-provided images and MP3 files excluded from Git

## Quick Start

```bash
# Bootstrap Git if this is a fresh Raspberry Pi OS install
sudo apt-get update
sudo apt-get install -y git

# Clone and check out this branch
cd /tmp
git clone https://github.com/jpk300/bluesgoal.git bluesgoal
cd bluesgoal
git checkout v2.1.0

# Install system dependencies from the repo helper script
sudo scripts/install_prereqs.sh

# Deploy this branch directly into Apache's document root
sudo rsync -a --delete --exclude .git --exclude mp3 --exclude images --exclude logs ./ /var/www/html/

# Create local asset/app runtime directories and apply permissions
sudo scripts/setup_permissions.sh

# Add your required image and audio assets, then open:
# http://bluesgoal.home.local
# or http://<raspberry-pi-ip>
```

## Features

### Audio & Strobe Control
- **5 Goal Horn Variations**: Power Play, Winter Classic, Old School, Marching In, Marching In (Glenn)
- **LED Strobing Effects**: GPIO pins 7 and 8 drive active-low relay-controlled lights
- **Stop Button**: Immediately halts active `mpg321` playback and turns relays off
- **Volume Control**: Adjusts ALSA `PCM` volume in 5 dB increments

### User Experience
- **Responsive Mobile-First UI**: Touch-optimized for tablets and phones
- **Visual Feedback**: Button processing state, notifications, and periodic status polling
- **Audio Status Indicator**: Shows whether an `mpg321` process is currently running
- **Activity Logging**: JSON-lines history of web UI and NHL worker actions

### Smart Features
- **Action Locking**: Prevents overlapping horn actions while a horn script is running
- **Real-Time Status API**: Reports current volume and audio playback state as JSON
- **NHL API Integration**: Optional background worker for automatic goal detection
- **Settings Page**: Web-based NHL feed enable/disable and source-team selection

## Hardware Requirements

- Raspberry Pi with GPIO header (tested targets: RPi 2B+, 3B+, 4B)
- LED strobe/relay wiring connected to physical BOARD pins 7 and 8
- Audio output supported by ALSA
- Network connection for web access and optional NHL API polling

## Software Requirements

### System Packages

From the repository root, install required OS packages with:

```bash
sudo scripts/install_prereqs.sh
```

Manual equivalent:

```bash
sudo apt-get update
sudo apt-get install python3 git apache2 php mpg321 alsa-utils python3-rpi.gpio rsync
```

Package notes:
- `python3-rpi.gpio` is required for GPIO pin control.
- `mpg321` is used for MP3 playback.
- `alsa-utils` provides `amixer`, which the status and volume scripts use.
- `rsync` is used by the recommended deploy command.

### Python Packages

No additional Python package is required for the active v2.1.0 scripts. Some legacy files under `goalhorn/volume/old_volume_controls/` reference `alsaaudio`, but current volume control uses `amixer` through `subprocess`.

## Installation & Setup

### 1. Deploy to Apache Document Root

v2.1.0 assumes the app is served directly from `/var/www/html`.

```bash
cd /tmp
git clone https://github.com/jpk300/bluesgoal.git bluesgoal
cd bluesgoal
git checkout v2.1.0
sudo rsync -a --delete --exclude .git --exclude mp3 --exclude images --exclude logs ./ /var/www/html/
```

If `/var/www/html` contains Apache's default `index.html`, back it up before deploying if you want to keep it.

### 2. Configure Apache2

Ensure Apache2 is running and serving `/var/www/html`:

```bash
sudo systemctl start apache2
sudo systemctl enable apache2
sudo systemctl status apache2
```

### 3. Create Writable Runtime Directories

Use the repository helper script for the default `/var/www/html` deployment:

```bash
sudo scripts/setup_permissions.sh
```

The script creates `/var/www/html/images`, `/var/www/html/mp3`, `/var/www/html/logs`, `/var/lib/bluesgoal`, `/run/bluesgoal`, and `/var/log/bluesgoal`; applies the recommended ownership/permissions; removes existing `__pycache__` directories; and installs a `tmpfiles.d` rule for `/run/bluesgoal` when `systemd-tmpfiles` is available.

Manual equivalent:

```bash
sudo mkdir -p /var/www/html/mp3 /var/www/html/images /var/www/html/logs
sudo mkdir -p /var/lib/bluesgoal /run/bluesgoal /var/log/bluesgoal

# Application code/static files: Apache-readable, root/admin-writable
sudo chown -R root:root /var/www/html
sudo find /var/www/html -type d -exec chmod 755 {} \;
sudo find /var/www/html -type f -exec chmod 644 {} \;
sudo find /var/www/html -name '*.py' -exec chmod 755 {} \;
sudo find /var/www/html -path '*/scripts/*.sh' -exec chmod 755 {} \;

# Runtime and local asset directories: writable where the app needs it
sudo chown -R www-data:www-data /var/www/html/logs /var/www/html/mp3 /var/www/html/images
sudo chown www-data:www-data /var/lib/bluesgoal /run/bluesgoal /var/log/bluesgoal
sudo chmod 775 /var/lib/bluesgoal /run/bluesgoal /var/log/bluesgoal
```

Runtime directory usage:
- `/var/www/html/logs` stores web/app activity and error logs.
- `/var/lib/bluesgoal` stores durable NHL feed settings/state.
- `/run/bluesgoal` stores transient locks and worker status. Because `/run` is recreated on reboot, recreate this directory during startup if needed.
- `/var/log/bluesgoal` stores NHL worker logs.

Recommended ownership model:
- Keep application code owned by `root:root` and readable/executable by Apache; the web server does not need write access to `config.py`, PHP files, HTML, CSS, or backend code.
- Keep writable runtime directories owned by `www-data` for the current Apache/PHP execution model.
- Keep MP3/image assets readable by Apache. They may be owned by `www-data` if you copy/manage them as that user, but they only need to be writable when you are adding or replacing assets.
- Remove any `__pycache__` directories from `/var/www/html`; active web-invoked Python commands use `python3 -B` to avoid creating bytecode caches in the document root.

### 4. Add Required MP3 Audio Files

Audio files are intentionally not committed to Git. Add these files to `/var/www/html/mp3` unless you also update `config.py`:

```text
/var/www/html/mp3/powerplay.mp3
/var/www/html/mp3/bluesgoal_winterclassic.mp3
/var/www/html/mp3/bluesgoal_oldschool.mp3
/var/www/html/mp3/marching_in.mp3
/var/www/html/mp3/marching_in_glenn.mp3
```

### 5. Add Required Image Assets

Images are also excluded from Git. The current UI expects these files:

```text
/var/www/html/images/nhl_goal_logo.jpeg
/var/www/html/images/bluesgoal_logo.jpeg
/var/www/html/images/button_bluesgoal_powerplay.jpeg
/var/www/html/images/button_bluesgoal_winterclassic.jpeg
/var/www/html/images/button_bluesgoal_oldschool.jpeg
/var/www/html/images/button_bluesgoal_marching_in_glenn.jpeg
/var/www/html/images/button_bluesgoal_marching_in_2017.jpeg
/var/www/html/images/button_volume_down.jpeg
/var/www/html/images/button_stop.png
/var/www/html/images/button_volume_up.jpeg
```

A fresh clone without these files will still serve the pages, but the button/logo imagery will be broken until assets are copied in.

### 6. Configure Sudo Permissions

The current PHP endpoints execute Python scripts with `sudo` so GPIO operations can run with the required privileges. The broad compatibility setup is:

```bash
sudo visudo
```

```text
www-data ALL=(ALL) NOPASSWD: /usr/bin/python3
```

> **Security note:** This app is intended for a trusted home LAN, but passwordless `python3` for `www-data` is intentionally broad. A safer future setup is to use one root-owned action runner with an allowlist and restrict sudoers to that single runner, or move hardware control into a root-owned systemd service.

Avoid granting `/usr/bin/python` unless you still need Python 2 legacy scripts. The active v2.1.0 scripts use Python 3.

### 7. Set File Permissions

For a fresh install, run the helper script after deploying files and creating the runtime directories:

```bash
sudo scripts/setup_permissions.sh
```

If the app is installed somewhere other than `/var/www/html`, override the document root:

```bash
sudo DOC_ROOT=/path/to/bluesgoal scripts/setup_permissions.sh
```

Manual equivalent:

```bash
# Code and static files: readable by Apache, writable only by root/admins
sudo chown -R root:root /var/www/html
sudo find /var/www/html -type d -exec chmod 755 {} \;
sudo find /var/www/html -type f -exec chmod 644 {} \;
sudo find /var/www/html -name '*.py' -exec chmod 755 {} \;
sudo find /var/www/html -path '*/scripts/*.sh' -exec chmod 755 {} \;

# Runtime and local asset directories: writable by the web app where needed
sudo chown -R www-data:www-data /var/www/html/logs /var/www/html/mp3 /var/www/html/images
sudo chown www-data:www-data /var/lib/bluesgoal /run/bluesgoal /var/log/bluesgoal
sudo chmod 775 /var/lib/bluesgoal /run/bluesgoal /var/log/bluesgoal

# Optional cleanup if Python bytecode caches were created during manual testing
sudo find /var/www/html -type d -name __pycache__ -prune -exec rm -rf {} +
```

If you already have a working `/var/www/html` install and only need to correct permissions like the screenshot, use this exact migration block:

```bash
# 1. Make the deployed application tree root-owned, readable by Apache,
#    and executable/searchable where directories or Python scripts need it.
sudo chown -R root:root /var/www/html
sudo find /var/www/html -type d -exec chmod 755 {} \;
sudo find /var/www/html -type f -exec chmod 644 {} \;
sudo find /var/www/html -name '*.py' -exec chmod 755 {} \;
sudo find /var/www/html -path '*/scripts/*.sh' -exec chmod 755 {} \;

# 2. Restore write ownership only for local assets and web/app logs.
sudo mkdir -p /var/www/html/images /var/www/html/mp3 /var/www/html/logs
sudo chown -R www-data:www-data /var/www/html/images /var/www/html/mp3 /var/www/html/logs
sudo find /var/www/html/images /var/www/html/mp3 /var/www/html/logs -type d -exec chmod 755 {} \;
sudo find /var/www/html/images /var/www/html/mp3 /var/www/html/logs -type f -exec chmod 644 {} \;

# 3. Ensure runtime state/log directories exist and are writable by the web app.
sudo mkdir -p /var/lib/bluesgoal /run/bluesgoal /var/log/bluesgoal
sudo chown www-data:www-data /var/lib/bluesgoal /run/bluesgoal /var/log/bluesgoal
sudo chmod 775 /var/lib/bluesgoal /run/bluesgoal /var/log/bluesgoal

# 4. Remove Python bytecode caches from the web root.
sudo find /var/www/html -type d -name __pycache__ -prune -exec rm -rf {} +
```

After either block, validate the setup:

```bash
# Confirm code is not writable by www-data, but Apache can read it.
ls -ld /var/www/html /var/www/html/goalhorn /var/www/html/config /var/www/html/stylesheets
ls -l /var/www/html/config.py /var/www/html/index.html /var/www/html/settings.html

# Confirm only app runtime/asset directories are www-data writable.
ls -ld /var/www/html/images /var/www/html/mp3 /var/www/html/logs /var/lib/bluesgoal /run/bluesgoal /var/log/bluesgoal

# Confirm sudo and status endpoint behavior.
sudo -u www-data sudo -n python3 -B -c 'print("sudo ok")'
curl -s http://localhost/goalhorn/_status.php
```

Expected ownership summary:

```text
/var/www/html                         root:root      drwxr-xr-x
/var/www/html/config.py               root:root      -rwxr-xr-x
/var/www/html/index.html              root:root      -rw-r--r--
/var/www/html/settings.html           root:root      -rw-r--r--
/var/www/html/config                  root:root      drwxr-xr-x
/var/www/html/goalhorn                root:root      drwxr-xr-x
/var/www/html/stylesheets             root:root      drwxr-xr-x
/var/www/html/images                  www-data:www-data drwxr-xr-x
/var/www/html/mp3                     www-data:www-data drwxr-xr-x
/var/www/html/logs                    www-data:www-data drwxr-xr-x
/var/lib/bluesgoal                    www-data:www-data drwxrwxr-x
/run/bluesgoal                        www-data:www-data drwxrwxr-x
/var/log/bluesgoal                    www-data:www-data drwxrwxr-x
```

## Usage

### Accessing the Web Interface

Via mDNS hostname, if configured:

```text
http://bluesgoal.home.local
```

Or by IP address:

```text
http://<raspberry-pi-ip>
```

### Main Interface (`index.html`)

- **Goal Horn Buttons**: Trigger a horn sound and GPIO strobe action.
- **Volume Controls**: Adjust ALSA `PCM` volume by 5 dB.
- **Stop Button**: Kills active `mpg321` playback and turns relays off.
- **Audio Indicator**: Polls `_status.php` and turns green when audio is playing.
- **Settings Link**: Opens NHL feed settings.

### Settings Page (`settings.html`)

Configure NHL API integration:
- Enable or disable automatic goal detection.
- Select the NHL source team to monitor.
- View worker status, polling frequency, watched game, and next scheduled game.

## Project Structure

```text
bluesgoal/
├── README.md                  # This file
├── config.py                  # Intended central configuration settings
├── logger.py                  # Activity/error logging helpers
├── log_activity.py            # CLI bridge used by PHP logging helpers
├── index.html                 # Main web interface
├── settings.html              # NHL API configuration page
├── .gitignore                 # Excludes local image/audio assets
│
├── stylesheets/
│   └── main.css               # Responsive CSS styling
│
├── scripts/
│   ├── install_prereqs.sh     # Installs Debian/Raspberry Pi OS packages
│   └── setup_permissions.sh   # Creates runtime dirs and applies permissions
│
├── images/                    # Required local image assets, not committed
│
├── mp3/                       # Required local audio assets, not committed
│
├── logs/                      # Activity/error logs, created during setup
│   ├── history.log            # JSON-lines activity log
│   └── error.log              # JSON-lines error log
│
├── goalhorn/                  # Apache endpoints and backend scripts
│   ├── action_runner.py       # Shared GPIO/audio runner for goal horn sounds
│   ├── _helpers.php           # Shared PHP JSON/logging/action helpers
│   ├── _powerplay.php
│   ├── _bluesgoal_winterclassic.php
│   ├── _bluesgoal_oldschool.php
│   ├── _marching_in.php
│   ├── _marching_in_glenn.php
│   ├── _stop.php
│   ├── _status.php
│   ├── _volume_up.php
│   ├── _volume_down.php
│   ├── _nhl_feed.php
│   ├── powerplay/
│   ├── bluesgoal_oldschool/
│   ├── bluesgoal_winterclassic/
│   ├── marching_in/
│   ├── marching_in_glenn/
│   ├── status/
│   ├── stop/
│   ├── volume/
│   ├── nhl_feed/
│   └── unused/                # Deprecated/legacy scripts
│
└── testscripts/               # Manual hardware/audio test utilities
    ├── test_gpio_alternating.py
    ├── test_gpio_simutaneous.py  # Current v2.1.0 filename keeps this typo
    └── test_music.py
```

## How It Works

### Manual Button Flow

1. The user taps a control on `index.html`.
2. JavaScript prevents page navigation and sends a `fetch()` request to the corresponding PHP endpoint.
3. The PHP helper attempts to acquire `/run/bluesgoal/action.lock` for horn actions.
4. The PHP endpoint logs the action and runs `goalhorn/action_runner.py` with a validated sound action using non-interactive `sudo -n python3 -B`. The `-B` flag prevents Python bytecode caches in the web root.
5. The shared action runner loads `config.py`, validates the requested action against `SOUNDS`, resolves the MP3 path, configures BOARD pins 7 and 8 as outputs, drives them LOW to activate active-low relays, stops any existing `mpg321` process, starts the selected MP3, keeps relays active for the configured duration, drives pins HIGH, and cleans up GPIO.
6. Stop and volume endpoints do not use the horn-action lock, so they can interrupt/adjust playback.
7. PHP returns a JSON response to the browser.
8. The frontend shows a notification and refreshes status from `_status.php`.

### NHL API Integration (Optional)

When enabled, the PHP settings endpoint starts a background Python worker that:

1. Reads the selected source team from `/var/lib/bluesgoal/nhl_feed_settings.json`.
2. Polls the NHL API for schedule and play-by-play data.
3. Establishes a baseline of already-seen goal events to avoid replaying old goals.
4. Triggers the Winter Classic horn through the shared action runner when a new goal for the selected team is detected.
5. Writes transient status to `/run/bluesgoal/nhl_feed_status.json`, durable state to `/var/lib/bluesgoal/nhl_feed_state.json`, worker logs to `/var/log/bluesgoal/nhl_feed.log`, and app activity to `/var/www/html/logs/history.log`.

> **Runtime-state note:** v2.1.0 uses `/var/lib/bluesgoal` for durable NHL feed state/settings, `/run/bluesgoal` for transient locks/status, and `/var/log/bluesgoal` for NHL worker logs. Legacy `/tmp/bluesgoal_*` files may be copied forward if present, but `/tmp` is no longer the active runtime location.

## Configuration

`config.py` is intended to centralize key settings:

```python
BASE_PATH = os.environ.get('BLUESGOAL_BASE_PATH', '/var/www/html')
MP3_DIR = os.environ.get('BLUESGOAL_MP3_DIR', os.path.join(BASE_PATH, 'mp3'))
LOG_DIR = os.environ.get('BLUESGOAL_LOG_DIR', os.path.join(BASE_PATH, 'logs'))
RELAY_PINS = [7, 8]
RELAY_ACTIVE_LOW = True
RELAY_DURATION = 30
AUDIO_CARD = os.environ.get('BLUESGOAL_AUDIO_CARD', '1')
VOLUME_STEP = os.environ.get('BLUESGOAL_VOLUME_STEP', '5dB')
AUDIO_PLAYER = os.environ.get('BLUESGOAL_AUDIO_PLAYER', 'mpg321')
SOUNDS = {
    'powerplay': 'powerplay.mp3',
    'bluesgoal_winterclassic': 'bluesgoal_winterclassic.mp3',
    'bluesgoal_oldschool': 'bluesgoal_oldschool.mp3',
    'marching_in': 'marching_in.mp3',
    'marching_in_glenn': 'marching_in_glenn.mp3',
}
```

> **Current limitation:** Goal horn sound actions, status, stop, and volume scripts use `config.py` for the shared values above. Some PHP entrypoints still hard-code `/var/www/html` when invoking scripts, and the ALSA mixer control name is still `PCM`; if changing install paths or mixer controls, search the codebase for those hard-coded values until the remaining config refactor is complete.

## GPIO Pin Usage

- **Physical BOARD pin 7**: LED strobe relay control
- **Physical BOARD pin 8**: LED strobe relay control

Both pins use active-low relay logic:
- **HIGH (3.3V)** = relay OFF / lights off
- **LOW (0V)** = relay ON / lights active

The horn scripts currently keep both relays active for about 30 seconds.

## Logging & Activity History

Actions and errors are stored as JSON lines:

```bash
# View real-time activity log
tail -f /var/www/html/logs/history.log

# Count actions by type
jq -r '.action' /var/www/html/logs/history.log | sort | uniq -c

# Pretty-print the log
jq . /var/www/html/logs/history.log
```

Sample log entry:

```json
{
  "timestamp": "2026-05-29 14:44:38",
  "action": "powerplay",
  "message": "Power Play has finished",
  "source": "web_ui"
}
```

## API Endpoints

### Real-Time Status API

```bash
curl http://bluesgoal.home.local/goalhorn/_status.php
```

Current response shape:

```json
{
  "success": true,
  "data": {
    "volume": 85,
    "audio_playing": false
  },
  "timestamp": "2026-05-29 14:44:38"
}
```

`volume` may be the string `"unknown"` if `amixer` fails or the expected mixer output cannot be parsed.

### NHL Feed API

Get NHL feed status and configuration:

```bash
curl http://bluesgoal.home.local/goalhorn/_nhl_feed.php
```

Example response:

```json
{
  "success": true,
  "enabled": true,
  "running": true,
  "settings": {
    "source_team": "STL"
  },
  "teams": ["ANA", "BOS", "BUF", "CAR", "STL"],
  "message": "NHL API feed enabled",
  "data": {
    "enabled": true,
    "running": true,
    "source_team": "STL",
    "mode": "live",
    "message": "Watching live play-by-play",
    "current_poll_seconds": 3,
    "last_poll_at": "2026-05-29T20:15:30+00:00"
  },
  "timestamp": "2026-05-29 15:15:30"
}
```

Enable/disable the feed:

```bash
curl -X POST http://bluesgoal.home.local/goalhorn/_nhl_feed.php \
  -H 'Content-Type: application/json' \
  -d '{"enabled": true}'
```

Change source team:

```bash
curl -X POST http://bluesgoal.home.local/goalhorn/_nhl_feed.php \
  -H 'Content-Type: application/json' \
  -d '{"source_team": "STL"}'
```

## Testing

The project includes manual test scripts for Raspberry Pi hardware/audio checks:

```bash
# Test alternating GPIO pattern on pins 7 and 8
sudo python3 /var/www/html/testscripts/test_gpio_alternating.py

# Test simultaneous GPIO pattern on pins 7 and 8
# Note: filename is misspelled in v2.1.0.
sudo python3 /var/www/html/testscripts/test_gpio_simutaneous.py

# Test audio playback with all MP3 files
python3 /var/www/html/testscripts/test_music.py
```

There is not yet a non-hardware automated regression test suite. Recommended future tests include NHL payload parsing, duplicate goal suppression, status JSON shape, logger behavior, and action command construction with mocked GPIO/subprocess calls.

## Troubleshooting

### Audio Not Playing

- Verify MP3 files exist in `/var/www/html/mp3/`.
- Check that `mpg321` is installed: `which mpg321`.
- Test manual playback: `mpg321 /var/www/html/mp3/powerplay.mp3`.
- Verify the Raspberry Pi audio output device is configured correctly.
- Check ALSA cards: `cat /proc/asound/cards`.
- Test the music script: `python3 /var/www/html/testscripts/test_music.py`.

### LEDs Not Strobing

- Verify GPIO pins 7 and 8 are wired to the relay inputs.
- Check that `python3-rpi.gpio` is installed: `dpkg -l | grep rpi.gpio`.
- Reinstall if needed: `sudo apt install python3-rpi.gpio`.
- Test GPIO import: `python3 -c "import RPi.GPIO as GPIO; print(GPIO.VERSION)"`.
- Run the manual GPIO test scripts.
- Ensure sudoers is configured for `www-data` if running from the web UI.
- Check relay wiring for active-low logic: HIGH = off, LOW = on.

### Page Not Loading

- Verify Apache2 is running: `sudo systemctl status apache2`.
- Confirm the app was deployed directly under `/var/www/html`.
- Check file permissions: `ls -la /var/www/html`.
- Review Apache errors: `sudo tail -f /var/log/apache2/error.log`.

### Images Missing or Broken

- Confirm `/var/www/html/images` exists.
- Confirm all required image assets listed above are present.
- Check browser developer tools for missing `404` image requests.

### Volume Control Not Working

- Check ALSA mixer setup: `alsamixer`.
- Verify available cards: `cat /proc/asound/cards`.
- Test the hard-coded current command: `amixer -c 1 set PCM 5dB+`.
- If your card/control differs, update the volume and status scripts or complete the config refactor.

### Status API Returns `unknown` Volume

- Check current command output: `amixer -c 1 get PCM`.
- Confirm the output contains a percentage such as `[85%]`.
- Confirm the correct ALSA card/control for your device. If the card differs, set `BLUESGOAL_AUDIO_CARD` for the Apache/PHP environment or update `AUDIO_CARD` in `config.py`. The mixer control name is currently `PCM`.

### Action Lock / “Wait for current action to complete”

- This is expected while a horn action is already running.
- The lock file is `/run/bluesgoal/action.lock`.
- Horn scripts currently keep relays active for about 30 seconds.
- Use Stop if you need to interrupt playback.

### NHL Feed Polling Errors

When the settings page shows `Waiting for worker status`, `Starting worker`, or `Worker unavailable`, check these in order:

```bash
# 1. Read the feed endpoint status
curl -s http://bluesgoal.home.local/goalhorn/_nhl_feed.php | jq .

# 2. Inspect the worker status file
sudo cat /run/bluesgoal/nhl_feed_status.json | jq .

# 3. Verify the feed is enabled (1 = enabled)
sudo cat /var/lib/bluesgoal/nhl_feed_enabled

# 4. Confirm the worker process is running
pgrep -af 'goalhorn/nhl_feed/nhl_feed.py'

# 5. Watch worker startup logs
sudo tail -f /var/log/bluesgoal/nhl_feed.log

# 6. Watch NHL-specific activity entries
sudo tail -f /var/www/html/logs/history.log | grep nhl

# 7. Check app-level logger errors
sudo tail -f /var/www/html/logs/error.log

# 8. Check Apache/PHP errors
sudo tail -f /var/log/apache2/error.log

# 9. Verify sudoers is configured for Python
sudo -u www-data sudo -n python3 -B -c 'print("sudo ok")'
```

If sudoers verification fails, revisit the sudoers setup and ensure `www-data` has passwordless access to `/usr/bin/python3`. After fixing, toggle the NHL API feed off and back on in settings.

**Note on `/run/bluesgoal`:** `/run` is usually recreated on reboot. If action locking or NHL feed status fails after a restart, recreate `/run/bluesgoal` with the runtime-directory commands above, or add a `tmpfiles.d` rule/startup step to create it automatically. The most reliable live status check is usually:

```bash
curl -s http://localhost/goalhorn/_nhl_feed.php | jq .
```

Optional `tmpfiles.d` rule for reboot-safe runtime directory creation:

```bash
printf 'd /run/bluesgoal 0775 www-data www-data -\n' | sudo tee /etc/tmpfiles.d/bluesgoal.conf
sudo systemd-tmpfiles --create /etc/tmpfiles.d/bluesgoal.conf
```

## Known Maintenance Items

These are known v2.1.0 cleanup opportunities:

1. Finish removing hard-coded `/var/www/html` paths from PHP entrypoints and deployment docs.
2. Replace broad `www-data` passwordless Python sudo with a narrow runner-specific sudo rule or systemd service.
3. Rename `test_gpio_simutaneous.py` to `test_gpio_simultaneous.py`.
4. Add non-hardware automated tests.
5. Rotate or bound activity/error logs.
6. Split inline JavaScript/CSS into static assets as the UI grows.
7. Add startup automation, such as `tmpfiles.d`, to recreate `/run/bluesgoal` after reboot.

## Recent Updates

### v2.1.0 (Latest)
- NHL API integration for automatic goal detection and horn triggering
- Settings page for source-team selection and feed control
- Background Python worker for NHL API polling
- Worker status monitoring in the settings page
- Enhanced activity logging for NHL API events
- Shared Python action runner for goal horn GPIO/audio behavior
- Improved troubleshooting documentation

### v2.0.0
- JSON PHP responses instead of browser redirects
- Python 3 migration for active scripts
- Action locking to prevent overlapping horn triggers
- Real-time volume display and audio status indicator
- Activity logging in JSON-lines format
- Central `config.py` introduced for future consolidation
- Responsive design improvements

## Notes

- Default local hostname: `bluesgoal.home.local` if configured through DNS, mDNS, or `/etc/hosts`.
- The app is intended for trusted local LAN use only.
- Current active scripts use `mpg321`, `amixer`, and `python3-rpi.gpio`.
- Local image and audio assets are excluded from Git by `.gitignore`.
- NHL API durable state lives in `/var/lib/bluesgoal`, transient locks/status live in `/run/bluesgoal`, and worker logs live in `/var/log/bluesgoal`.

## License

Personal project - feel free to adapt for your own use.

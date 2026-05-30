# St. Louis Blues Goal Horn Web App

**Last updated:** May 30, 2026
**Current Version:** v2.1.0

A local Raspberry Pi web app for St. Louis Blues goal celebrations. The app provides a touch-friendly Apache/PHP interface that triggers goal horn audio, GPIO-controlled LED strobes, stop and volume controls, activity logging, and optional NHL API goal detection.

> **Deployment assumption:** v2.1.0 expects the application files to live directly in Apache's default document root: `/var/www/html`. Several scripts still use hard-coded `/var/www/html/...` paths, so installing into `/var/www/html/bluesgoal` requires code/config changes or symlinks.

## Overview

This project is a small Python/PHP application intended for a trusted home LAN. PHP endpoints receive button/API requests from the web UI, then invoke Python scripts that control audio playback, Raspberry Pi GPIO pins, volume, logging, and the optional NHL feed worker.

**Primary components:**
- **Python** - Audio, GPIO, status, logging, volume, and NHL worker logic
- **PHP** - Apache-accessible JSON endpoints and action dispatch
- **HTML/CSS/JavaScript** - Main control page and settings page
- **Local assets** - User-provided images and MP3 files excluded from Git

## Quick Start

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3 git apache2 php mpg321 alsa-utils python3-rpi.gpio rsync

# Deploy this branch directly into Apache's document root
cd /tmp
git clone https://github.com/jpk300/bluesgoal.git bluesgoal
cd bluesgoal
git checkout v2.1.0
sudo rsync -a --delete --exclude .git --exclude mp3 --exclude images --exclude logs ./ /var/www/html/

# Create local asset/runtime directories
sudo mkdir -p /var/www/html/mp3 /var/www/html/images /var/www/html/logs
sudo mkdir -p /var/lib/bluesgoal /var/log/bluesgoal /run/bluesgoal
sudo chown -R www-data:www-data /var/www/html/logs /var/lib/bluesgoal /var/log/bluesgoal /run/bluesgoal
sudo chmod 755 /var/www/html/logs /var/lib/bluesgoal /var/log/bluesgoal
sudo chmod 775 /run/bluesgoal
echo 'd /run/bluesgoal 0775 www-data www-data -' | sudo tee /etc/tmpfiles.d/bluesgoal.conf
sudo systemd-tmpfiles --create /etc/tmpfiles.d/bluesgoal.conf

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

```bash
sudo mkdir -p /var/www/html/logs /var/www/html/mp3 /var/www/html/images
sudo mkdir -p /var/lib/bluesgoal /var/log/bluesgoal /run/bluesgoal
sudo chown -R www-data:www-data /var/www/html/logs /var/lib/bluesgoal /var/log/bluesgoal /run/bluesgoal
sudo chmod 755 /var/www/html/logs /var/lib/bluesgoal /var/log/bluesgoal
sudo chmod 775 /run/bluesgoal

# Recreate /run/bluesgoal after reboot
echo 'd /run/bluesgoal 0775 www-data www-data -' | sudo tee /etc/tmpfiles.d/bluesgoal.conf
sudo systemd-tmpfiles --create /etc/tmpfiles.d/bluesgoal.conf
```

Recommended ownership model:
- Keep application code readable/executable by Apache, but not necessarily owned by `www-data`.
- Keep web activity logs in `/var/www/html/logs` owned by `www-data`.
- Keep NHL durable state in `/var/lib/bluesgoal`, transient locks/status in `/run/bluesgoal`, and worker logs in `/var/log/bluesgoal`, owned by `www-data`.
- Keep MP3/image assets readable by Apache.

### 4. Add Required MP3 Audio Files

Audio files are intentionally not committed to Git. Add these files to `/var/www/html/mp3` unless you also update `config.py` and the legacy hard-coded script paths:

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

```bash
sudo find /var/www/html -type d -exec chmod 755 {} \;
sudo find /var/www/html -type f -exec chmod 644 {} \;
sudo find /var/www/html -name '*.py' -exec chmod 755 {} \;
sudo chown -R www-data:www-data /var/www/html/logs
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
├── config/
│   └── nhl_teams.json         # Shared NHL team allowlist/labels for PHP and Python
│
├── stylesheets/
│   └── main.css               # Responsive CSS styling
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
4. The PHP endpoint logs the action and runs the relevant Python script with `sudo python3`.
5. Horn scripts configure BOARD pins 7 and 8 as outputs, drive them LOW to activate active-low relays, stop any existing `mpg321` process, start the selected MP3, keep relays active for about 30 seconds, drive pins HIGH, and clean up GPIO.
6. Stop and volume endpoints do not use the horn-action lock, so they can interrupt/adjust playback.
7. PHP returns a JSON response to the browser.
8. The frontend shows a notification and refreshes status from `_status.php`.

### NHL API Integration (Optional)

When enabled, the PHP settings endpoint starts a background Python worker that:

1. Reads the selected source team from `/var/lib/bluesgoal/nhl_feed_settings.json`.
2. Polls the NHL API for schedule and play-by-play data.
3. Establishes a baseline of already-seen goal events to avoid replaying old goals.
4. Triggers the Winter Classic horn when a new goal for the selected team is detected.
5. Writes status to `/run/bluesgoal/nhl_feed_status.json`, durable worker state to `/var/lib/bluesgoal`, worker logs to `/var/log/bluesgoal/nhl_feed.log`, and activity events to `/var/www/html/logs/history.log`.

> **Runtime-state note:** v2.1.0 stores durable NHL settings/state in `/var/lib/bluesgoal`, transient status/locks in `/run/bluesgoal`, and worker logs in `/var/log/bluesgoal`. The PHP endpoint and Python worker also attempt a one-time copy from the legacy `/tmp/bluesgoal_*` files if the new files do not exist yet.

## Configuration

`config.py` is intended to centralize key settings:

```python
BASE_PATH = '/var/www/html'
MP3_DIR = os.path.join(BASE_PATH, 'mp3')
LOG_DIR = os.path.join(BASE_PATH, 'logs')
RELAY_PINS = [7, 8]
RELAY_ACTIVE_LOW = True
RELAY_DURATION = 30
AUDIO_CARD = 1
VOLUME_STEP = '5dB'
AUDIO_PLAYER = 'mpg321'
SOUNDS = {
    'powerplay': 'powerplay.mp3',
    'bluesgoal_winterclassic': 'bluesgoal_winterclassic.mp3',
    'bluesgoal_oldschool': 'bluesgoal_oldschool.mp3',
    'marching_in': 'marching_in.mp3',
    'marching_in_glenn': 'marching_in_glenn.mp3',
}
```

> **Current limitation:** Some v2.1.0 scripts still hard-code `/var/www/html`, `mpg321`, GPIO pins, ALSA card `1`, and `PCM`. If changing install paths, pins, mixer devices, or player commands, search the codebase for those hard-coded values until the planned shared action runner refactor is complete.

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

`volume` may be the string `"unknown"` if `amixer` fails or the expected mixer output cannot be parsed. The NHL feed endpoint also returns `team_labels` from `config/nhl_teams.json`, which is the shared PHP/Python team source of truth.

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
  "team_labels": {
    "ANA": "Anaheim Ducks",
    "BOS": "Boston Bruins",
    "STL": "St. Louis Blues"
  },
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
- Confirm the correct ALSA card/control for your device.

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
sudo -u www-data sudo -n python3 -c 'print("sudo ok")'
```

If sudoers verification fails, revisit the sudoers setup and ensure `www-data` has passwordless access to `/usr/bin/python3`. After fixing, toggle the NHL API feed off and back on in settings.

**Note on `/run/bluesgoal`:** `/run` is recreated on reboot. If the NHL feed cannot write status or action locks after a reboot, verify the tmpfiles rule and recreate the runtime directory:

```bash
sudo systemd-tmpfiles --create /etc/tmpfiles.d/bluesgoal.conf
ls -ld /run/bluesgoal
curl -s http://localhost/goalhorn/_nhl_feed.php | jq .
```

## Known Maintenance Items

These are known v2.1.0 cleanup opportunities:

1. Replace duplicated horn scripts with one shared Python action runner.
2. Use `config.py` consistently instead of hard-coded paths/pins/audio settings.
3. Replace broad `www-data` passwordless Python sudo with a narrow runner or systemd service.
4. Add PID-file based NHL worker detection instead of `pgrep -f`.
5. Rename `test_gpio_simutaneous.py` to `test_gpio_simultaneous.py`.
6. Add non-hardware automated tests.
7. Rotate or bound activity/error logs.
8. Split inline JavaScript/CSS into static assets as the UI grows.

## Recent Updates

### v2.1.0 (Latest)
- NHL API integration for automatic goal detection and horn triggering
- Settings page for source-team selection and feed control
- Background Python worker for NHL API polling
- Worker status monitoring in the settings page
- Enhanced activity logging for NHL API events
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
- NHL API durable state lives in `/var/lib/bluesgoal`; transient status and locks live in `/run/bluesgoal`; worker logs live in `/var/log/bluesgoal`.

## License

Personal project - feel free to adapt for your own use.

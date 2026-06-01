# St. Louis Blues Goal Horn Web App

**Last updated:** May 30, 2026  
**Current version:** v2.1.0 local

A local Raspberry Pi web app for St. Louis Blues goal celebrations. It provides a touch-friendly Apache/PHP interface for goal horn audio, GPIO-controlled relay strobes, stop and volume controls, activity logging, and optional NHL API goal detection.

This app is designed for a trusted home LAN. It is not hardened for internet exposure.

## Overview

BluesGoal is intentionally small:

- **HTML/CSS/JavaScript** renders the main control page and NHL settings page.
- **PHP endpoints** receive browser requests, return JSON, acquire locks, and dispatch Python scripts.
- **Python scripts** control MP3 playback, GPIO relay pins, ALSA volume, status reporting, logging, and the optional NHL feed worker.
- **Local assets** such as images and MP3 files are excluded from Git and copied onto the Raspberry Pi during setup.

The recommended deployment remains Apache's default document root, `/var/www/html`. The active PHP endpoints now resolve backend scripts relative to the app root, so non-default document roots are easier to support, but the default layout is still the least surprising path because examples, assets, logs, and some Python defaults use `/var/www/html`.

## Features

- Five goal horn actions:
  - Power Play
  - Winter Classic
  - Old School
  - Marching In
  - Marching In (Glenn)
- GPIO relay strobes on physical BOARD pins 7 and 8.
- Active-low relay support.
- Stop button that kills active `mpg321` playback and turns relays off.
- ALSA volume up/down controls using auto-detected mixer controls.
- Browser status polling for current volume and audio playback state.
- JSON-lines activity and error logs.
- Optional NHL API feed that triggers the Winter Classic horn for STL goals and the NHL horn for other selected teams.
- Optional systemd service installer so the NHL worker starts after reboot when enabled.

## Hardware Requirements

- Raspberry Pi with GPIO header, tested target family: Raspberry Pi 2B+, 3B+, and 4B.
- Relay or LED strobe wiring connected to physical BOARD pins 7 and 8.
- Audio output supported by ALSA.
- Network access for local browser clients.
- Internet access only if the optional NHL API feed is enabled.

## Software Requirements

Install the required Debian/Raspberry Pi OS packages with:

```bash
sudo scripts/install_prereqs.sh
```

Manual equivalent:

```bash
sudo apt-get update
sudo apt-get install -y python3 git apache2 php mpg321 alsa-utils python3-rpi.gpio rsync
```

Package notes:

- `python3-rpi.gpio` is required for GPIO control.
- `mpg321` is used for MP3 playback.
- `alsa-utils` provides `amixer`.
- `rsync` is used by the recommended deployment command.
- No additional Python package is required for active scripts.

## Quick Start

```bash
# Bootstrap Git if this is a fresh Raspberry Pi OS install.
sudo apt-get update
sudo apt-get install -y git

# Clone and check out the app.
cd /tmp
git clone https://github.com/jpk300/bluesgoal.git bluesgoal
cd bluesgoal

# Install prerequisites.
sudo scripts/install_prereqs.sh

# Deploy directly into Apache's document root.
sudo rsync -a --delete --exclude .git --exclude mp3 --exclude images --exclude logs ./ /var/www/html/

# Apply runtime directories and permissions from the deployed copy.
cd /var/www/html
sudo scripts/setup_permissions.sh

# Optional, recommended if you use NHL automation.
sudo scripts/install_nhl_feed_service.sh

# Add required MP3/image assets, then open:
# http://bluesgoal.home.local
# or http://<raspberry-pi-ip>
```

If `/var/www/html` contains Apache's default `index.html`, back it up before deploying if you want to keep it.

## Installation Details

### Apache

Ensure Apache is enabled and serving `/var/www/html`:

```bash
sudo systemctl start apache2
sudo systemctl enable apache2
sudo systemctl status apache2
```

### Runtime Directories And Permissions

Run:

```bash
sudo scripts/setup_permissions.sh
```

The script creates and configures:

- `/var/www/html/images` for local image assets.
- `/var/www/html/mp3` for local audio assets.
- `/var/www/html/logs` for web/app activity and error logs.
- `/var/lib/bluesgoal` for durable NHL feed settings and state.
- `/run/bluesgoal` for transient locks and worker status.
- `/var/log/bluesgoal` for NHL worker logs.

It also makes application code root-owned and Apache-readable, restores write ownership only for runtime/asset directories, removes Python bytecode caches, and installs a `tmpfiles.d` rule for `/run/bluesgoal` when `systemd-tmpfiles` is available.

For a non-default document root:

```bash
sudo DOC_ROOT=/path/to/bluesgoal scripts/setup_permissions.sh
```

Recommended ownership model:

- Application files: `root:root`, readable by Apache.
- Python scripts: executable by Apache/root.
- Runtime directories: writable by `www-data`.
- MP3/image assets: readable by Apache, writable only when you are adding or replacing assets.

Expected ownership summary for the default install:

```text
/var/www/html                         root:root          drwxr-xr-x
/var/www/html/config.py               root:root          -rwxr-xr-x
/var/www/html/index.html              root:root          -rw-r--r--
/var/www/html/settings.html           root:root          -rw-r--r--
/var/www/html/config                  root:root          drwxr-xr-x
/var/www/html/goalhorn                root:root          drwxr-xr-x
/var/www/html/stylesheets             root:root          drwxr-xr-x
/var/www/html/images                  www-data:www-data  drwxr-xr-x
/var/www/html/mp3                     www-data:www-data  drwxr-xr-x
/var/www/html/logs                    www-data:www-data  drwxr-xr-x
/var/lib/bluesgoal                    www-data:www-data  drwxrwxr-x
/run/bluesgoal                        www-data:www-data  drwxrwxr-x
/var/log/bluesgoal                    www-data:www-data  drwxrwxr-x
```

### Sudo Permissions

The web endpoints execute Python with `sudo` so GPIO operations can run with the required privileges. The current broad compatibility sudoers rule is:

```text
www-data ALL=(ALL) NOPASSWD: /usr/bin/python3
```

Add it with:

```bash
sudo visudo
```

This is acceptable for a trusted home LAN appliance, but it is intentionally broad. A future hardening improvement is to replace it with a root-owned allowlisted runner or systemd hardware-control service.

### NHL Feed Boot Service

If you use NHL automation, install the service:

```bash
sudo scripts/install_nhl_feed_service.sh
```

The installer:

- Writes `/etc/systemd/system/bluesgoal-nhl-feed.service`.
- Creates runtime directories if needed.
- Runs the worker as `www-data`.
- Enables the service at boot.
- Starts the service immediately.
- Appends stdout/stderr to `/var/log/bluesgoal/nhl_feed.log`.

Useful commands:

```bash
sudo systemctl status bluesgoal-nhl-feed.service
sudo journalctl -u bluesgoal-nhl-feed.service -f
sudo systemctl restart bluesgoal-nhl-feed.service
```

The service starts the worker at boot. The worker exits cleanly when the feed is disabled and continues running only while `/var/lib/bluesgoal/nhl_feed_enabled` contains `1`.

For a non-default document root:

```bash
sudo DOC_ROOT=/path/to/bluesgoal scripts/install_nhl_feed_service.sh
```

The service supports these environment overrides:

- `BLUESGOAL_DATA_DIR`, default `/var/lib/bluesgoal`
- `BLUESGOAL_RUN_DIR`, default `/run/bluesgoal`
- `BLUESGOAL_WORKER_LOG_DIR`, default `/var/log/bluesgoal`
- `BLUESGOAL_TIMEZONE`, default `America/Chicago`
- `BLUESGOAL_NHL_SERVICE_NAME`, default `bluesgoal-nhl-feed`

## Required Local Assets

Audio and images are intentionally excluded from Git.

### MP3 Files

Add these files to `/var/www/html/mp3` unless you override `BLUESGOAL_MP3_DIR`:

```text
powerplay.mp3
bluesgoal_winterclassic.mp3
bluesgoal_oldschool.mp3
marching_in.mp3
marching_in_glenn.mp3
nhl_horn.mp3
```

### Image Files

Add these files to `/var/www/html/images`:

```text
nhl_goal_logo.jpeg
bluesgoal_logo.jpeg
button_bluesgoal_powerplay.jpeg
button_bluesgoal_winterclassic.jpeg
button_bluesgoal_oldschool.jpeg
button_bluesgoal_marching_in_glenn.jpeg
button_bluesgoal_marching_in_2017.jpeg
button_volume_down.jpeg
button_stop.png
button_volume_up.jpeg
```

A fresh clone will serve the pages without these files, but button and logo imagery will be broken until the assets are copied in.

## Usage

Open the main interface:

```text
http://bluesgoal.home.local
```

or:

```text
http://<raspberry-pi-ip>
```

Main controls:

- Goal horn buttons trigger one sound and the relay strobe action.
- Stop interrupts active playback and turns relays off.
- Volume buttons adjust ALSA volume using the configured or auto-detected mixer control.
- The status indicator refreshes after actions, every five seconds while audio is playing, every 60 seconds while idle, and when a hidden browser tab becomes visible again.
- Settings opens NHL automation controls.

Settings page:

- Enable or disable NHL API goal detection.
- Select the source team to monitor.
- View worker status, polling frequency, watched game, next game, and trigger expectations.

## API Endpoints

### Manual Actions

Manual actions are side effects and require `POST`.

```bash
curl -X POST http://bluesgoal.home.local/goalhorn/_powerplay.php
curl -X POST http://bluesgoal.home.local/goalhorn/_bluesgoal_winterclassic.php
curl -X POST http://bluesgoal.home.local/goalhorn/_bluesgoal_oldschool.php
curl -X POST http://bluesgoal.home.local/goalhorn/_marching_in.php
curl -X POST http://bluesgoal.home.local/goalhorn/_marching_in_glenn.php
curl -X POST http://bluesgoal.home.local/goalhorn/_nhl_horn.php
curl -X POST http://bluesgoal.home.local/goalhorn/_stop.php
curl -X POST http://bluesgoal.home.local/goalhorn/_volume_up.php
curl -X POST http://bluesgoal.home.local/goalhorn/_volume_down.php
```

Successful response shape:

```json
{
  "success": true,
  "message": "Power Play has finished",
  "output": "...",
  "timestamp": "2026-05-30 12:00:00"
}
```

If an action is already running, horn endpoints return `409` with `retry_after`.

### Status API

```bash
curl http://bluesgoal.home.local/goalhorn/_status.php
```

Response shape:

```json
{
  "success": true,
  "data": {
    "volume": 85,
    "audio_playing": false
  },
  "timestamp": "2026-05-30 12:00:00"
}
```

`volume` may be `"unknown"` if `amixer` fails or the expected percentage cannot be parsed.

### NHL Feed API

Read feed status and configuration:

```bash
curl http://bluesgoal.home.local/goalhorn/_nhl_feed.php
```

Enable or disable the feed:

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

Important NHL feed files:

- Enabled flag: `/var/lib/bluesgoal/nhl_feed_enabled`
- Settings: `/var/lib/bluesgoal/nhl_feed_settings.json`
- Durable duplicate-goal state: `/var/lib/bluesgoal/nhl_feed_state.json`
- Live status: `/run/bluesgoal/nhl_feed_status.json`
- Worker log: `/var/log/bluesgoal/nhl_feed.log`

## How It Works

### Manual Button Flow

1. The user taps a control on `index.html`.
2. JavaScript sends a `POST` request to the corresponding PHP endpoint.
3. The PHP helper validates the method and acquires `/run/bluesgoal/action.lock` for horn actions.
4. The endpoint logs activity through `log_activity.py`.
5. The endpoint runs the selected Python script with `sudo -n python3 -B`.
6. `action_runner.py` validates the action against `SOUNDS`, resolves the MP3 path, configures GPIO, starts playback, keeps relays active for `RELAY_DURATION`, turns relays off, and cleans up GPIO.
7. PHP returns JSON to the browser.
8. The browser shows a notification and refreshes status.

Stop and volume actions do not use the horn-action lock so they can interrupt or adjust playback during a running horn action.

### NHL Feed Flow

When enabled, the NHL worker:

1. Reads the selected source team from `/var/lib/bluesgoal/nhl_feed_settings.json`.
2. Polls the NHL club schedule endpoint.
3. Sleeps until pregame watch time when a future game is found.
4. Polls play-by-play during pregame/live states.
5. Establishes a baseline of already-seen goal events so old goals are not replayed.
6. Triggers the Winter Classic horn for new STL goals or the NHL horn for goals by another selected team.
7. Stores seen event IDs in `/var/lib/bluesgoal/nhl_feed_state.json`.
8. Updates `/run/bluesgoal/nhl_feed_status.json` for the settings page.

`game_today` is calculated using `BLUESGOAL_TIMEZONE`, default `America/Chicago`, so Central Time evening games are represented correctly.

## Configuration

### Python App Configuration

`config.py` contains the active defaults for audio, GPIO, sound files, and web/app logs:

```python
BASE_PATH = os.environ.get('BLUESGOAL_BASE_PATH', '/var/www/html')
MP3_DIR = os.environ.get('BLUESGOAL_MP3_DIR', os.path.join(BASE_PATH, 'mp3'))
LOG_DIR = os.environ.get('BLUESGOAL_LOG_DIR', os.path.join(BASE_PATH, 'logs'))
RELAY_PINS = [7, 8]
RELAY_ACTIVE_LOW = True
RELAY_DURATION = 30
AUDIO_CARD = os.environ.get('BLUESGOAL_AUDIO_CARD', '0')
AUDIO_MIXER_CONTROL = os.environ.get('BLUESGOAL_AUDIO_MIXER_CONTROL', '')
VOLUME_STEP = os.environ.get('BLUESGOAL_VOLUME_STEP', '5dB')
AUDIO_PLAYER = os.environ.get('BLUESGOAL_AUDIO_PLAYER', 'mpg321')
```

Sound mapping:

```python
SOUNDS = {
    'powerplay': 'powerplay.mp3',
    'bluesgoal_winterclassic': 'bluesgoal_winterclassic.mp3',
    'bluesgoal_oldschool': 'bluesgoal_oldschool.mp3',
    'marching_in': 'marching_in.mp3',
    'marching_in_glenn': 'marching_in_glenn.mp3',
    'nhl_horn': 'nhl_horn.mp3',
}
```

### Runtime Environment Variables

Supported environment variables:

- `BLUESGOAL_BASE_PATH`, default `/var/www/html`
- `BLUESGOAL_MP3_DIR`, default `$BLUESGOAL_BASE_PATH/mp3`
- `BLUESGOAL_LOG_DIR`, default `$BLUESGOAL_BASE_PATH/logs`
- `BLUESGOAL_AUDIO_CARD`, default `0`
- `BLUESGOAL_AUDIO_MIXER_CONTROL`, default empty for auto-detect
- `BLUESGOAL_VOLUME_STEP`, default `5dB`
- `BLUESGOAL_AUDIO_PLAYER`, default `mpg321`
- `BLUESGOAL_DATA_DIR`, default `/var/lib/bluesgoal`
- `BLUESGOAL_RUN_DIR`, default `/run/bluesgoal`
- `BLUESGOAL_WORKER_LOG_DIR`, default `/var/log/bluesgoal`
- `BLUESGOAL_TIMEZONE`, default `America/Chicago`

Volume and status scripts auto-detect a mixer control from common names such as `PCM`, `Master`, `Headphone`, `Speaker`, and `Digital`. Set `BLUESGOAL_AUDIO_MIXER_CONTROL` if your device needs a specific mixer name.

## Project Structure

```text
bluesgoal/
|-- README.md
|-- config.py
|-- logger.py
|-- log_activity.py
|-- index.html
|-- settings.html
|-- .gitignore
|-- buildinfo/
|   `-- wiring_diagram.pdf
|-- config/
|   `-- nhl_teams.json
|-- scripts/
|   |-- install_prereqs.sh
|   |-- setup_permissions.sh
|   `-- install_nhl_feed_service.sh
|-- stylesheets/
|   `-- main.css
|-- testscripts/
|   |-- test_gpio_alternating.py
|   |-- test_gpio_simutaneous.py
|   `-- test_music.py
|-- mp3/
|   `-- local MP3 files, ignored by Git
`-- goalhorn/
    |-- _helpers.php
    |-- _powerplay.php
    |-- _bluesgoal_winterclassic.php
    |-- _bluesgoal_oldschool.php
    |-- _marching_in.php
    |-- _marching_in_glenn.php
    |-- _nhl_horn.php
    |-- _stop.php
    |-- _status.php
    |-- _volume_up.php
    |-- _volume_down.php
    |-- _nhl_feed.php
    |-- action_runner.py
    |-- status/
    |-- stop/
    |-- volume/
    |-- nhl_feed/
    |-- bluesgoal_oldschool/
    |-- bluesgoal_winterclassic/
    |-- marching_in/
    |-- marching_in_glenn/
    |-- nhl_horn/
    |-- powerplay/
    `-- unused/
```

Notes:

- `goalhorn/unused/` contains deprecated legacy endpoints/scripts.
- `goalhorn/volume/old_volume_controls/` contains legacy volume scripts, including scripts that reference `alsaaudio`; active volume control uses `amixer`.
- `testscripts/test_gpio_simutaneous.py` keeps the existing filename typo for compatibility.

## Logging

Activity log:

```bash
tail -f /var/www/html/logs/history.log
```

Error log:

```bash
tail -f /var/www/html/logs/error.log
```

NHL worker log:

```bash
sudo tail -f /var/log/bluesgoal/nhl_feed.log
```

Activity entries are JSON lines:

```json
{
  "timestamp": "2026-05-30 12:00:00",
  "action": "powerplay",
  "message": "Power Play has finished",
  "source": "web_ui"
}
```

## Testing

Manual hardware/audio tests:

```bash
sudo python3 /var/www/html/testscripts/test_gpio_alternating.py
sudo python3 /var/www/html/testscripts/test_gpio_simutaneous.py
python3 /var/www/html/testscripts/test_music.py
```

Recommended validation after deployment:

```bash
sudo -u www-data sudo -n python3 -B -c 'print("sudo ok")'
curl -s http://localhost/goalhorn/_status.php
curl -s http://localhost/goalhorn/_nhl_feed.php
sudo systemctl status bluesgoal-nhl-feed.service
```

There is not yet a non-hardware automated regression test suite. Good future tests would cover NHL payload parsing, duplicate-goal suppression, status JSON shape, logger behavior, and action command construction with mocked GPIO/subprocess calls.

## Troubleshooting

### Page Does Not Load

- Check Apache: `sudo systemctl status apache2`
- Check Apache errors: `sudo tail -f /var/log/apache2/error.log`
- Confirm deployment: `ls -la /var/www/html`
- Confirm PHP is installed: `php -v`

### Images Are Missing

- Confirm the files listed in Required Local Assets exist under `/var/www/html/images`.
- Check browser developer tools for `404` image requests.
- Confirm Apache can read the files.

### Audio Does Not Play

- Confirm MP3 files exist under `/var/www/html/mp3`.
- Check `mpg321`: `which mpg321`
- Test manual playback: `mpg321 /var/www/html/mp3/powerplay.mp3`
- Check ALSA cards: `cat /proc/asound/cards`
- Confirm the configured card in `BLUESGOAL_AUDIO_CARD` or `config.py`.

### Volume Control Fails

- Open `alsamixer` and confirm which mixer controls the device exposes.
- List controls: `amixer -c 1 scontrols`
- Test a specific control, for example: `amixer -c 1 set Master 5dB+`
- Test readback, for example: `amixer -c 1 get Master`
- If the command fails, the web endpoint should now return an action failure instead of false success.
- If your card number differs, set `BLUESGOAL_AUDIO_CARD` for the Apache/PHP environment or update `AUDIO_CARD` in `config.py`.
- If auto-detection picks the wrong control, set `BLUESGOAL_AUDIO_MIXER_CONTROL`, for example `Master`.

### LEDs Do Not Strobe

- Confirm relay wiring to physical BOARD pins 7 and 8.
- Confirm active-low relay behavior: HIGH means off, LOW means on.
- Check `python3-rpi.gpio`: `dpkg -l | grep rpi.gpio`
- Test import: `python3 -c "import RPi.GPIO as GPIO; print(GPIO.VERSION)"`
- Run the GPIO test scripts.
- Confirm `www-data` can run Python through sudo.

### Action Lock Message

If the UI reports that an action is already running:

- This is expected while a horn action owns `/run/bluesgoal/action.lock`.
- Horn actions keep relays active for about 30 seconds by default.
- Use Stop to interrupt playback.
- If the lock appears stuck after a crash, check for active Python/action processes before removing the lock file.

### NHL Feed Problems

Check these in order:

```bash
# Endpoint status
curl -s http://localhost/goalhorn/_nhl_feed.php | jq .

# Enabled flag, 1 means enabled
sudo cat /var/lib/bluesgoal/nhl_feed_enabled

# Worker service
sudo systemctl status bluesgoal-nhl-feed.service
sudo journalctl -u bluesgoal-nhl-feed.service -n 100

# Worker status and logs
sudo cat /run/bluesgoal/nhl_feed_status.json | jq .
sudo tail -f /var/log/bluesgoal/nhl_feed.log

# Process check
pgrep -af 'goalhorn/nhl_feed/nhl_feed.py'

# App and Apache logs
sudo tail -f /var/www/html/logs/history.log
sudo tail -f /var/www/html/logs/error.log
sudo tail -f /var/log/apache2/error.log

# Sudo check
sudo -u www-data sudo -n python3 -B -c 'print("sudo ok")'
```

If `/run/bluesgoal` is missing after reboot, rerun:

```bash
sudo scripts/setup_permissions.sh
```

or recreate the tmpfiles rule:

```bash
printf 'd /run/bluesgoal 0775 www-data www-data -\n' | sudo tee /etc/tmpfiles.d/bluesgoal.conf
sudo systemd-tmpfiles --create /etc/tmpfiles.d/bluesgoal.conf
```

## Maintenance Notes

Current cleanup opportunities:

1. Replace broad passwordless `www-data` Python sudo with a narrow runner-specific sudo rule or root-owned hardware-control service.
2. Add non-hardware automated tests.
3. Rename `test_gpio_simutaneous.py` to `test_gpio_simultaneous.py`.
4. Rotate or bound activity and error logs.
5. Split inline JavaScript/CSS out of HTML if the UI grows.
6. Remove or archive legacy scripts under `goalhorn/unused/` and `goalhorn/volume/old_volume_controls/` when no longer needed.

## Recent Changes

### v2.1.1 local

- PHP action/status endpoints resolve scripts relative to the app root instead of hard-coding `/var/www/html`.
- Manual action endpoints require `POST`.
- Main page action requests now use `POST`.
- Volume up/down scripts now return failures when `amixer` fails.
- NHL feed worker supports configurable runtime directories.
- NHL `game_today` is calculated in `BLUESGOAL_TIMEZONE`, default `America/Chicago`.
- Added `scripts/install_nhl_feed_service.sh` for reboot-safe NHL worker startup.
- README refreshed to match current repo behavior.

### v2.1.0

- NHL API integration for automatic goal detection and horn triggering.
- Settings page for source-team selection and feed control.
- Background Python worker for NHL API polling.
- Worker status monitoring in the settings page.
- Enhanced activity logging for NHL API events.
- Shared Python action runner for goal horn GPIO/audio behavior.
- Improved troubleshooting documentation.

### v2.0.0

- JSON PHP responses instead of browser redirects.
- Python 3 migration for active scripts.
- Action locking to prevent overlapping horn triggers.
- Real-time volume display and audio status indicator.
- Activity logging in JSON-lines format.
- Central `config.py` introduced for future consolidation.
- Responsive design improvements.

## License

Personal project. Adapt as needed for your own local setup.

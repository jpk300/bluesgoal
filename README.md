# St. Louis Blues Goal Horn Web App

**Last updated:** May 29, 2026

A web-based goal horn and celebration system running on a Raspberry Pi that plays music and triggers LED strobing effects when the St. Louis Blues score a goal.

## Overview

This application is a Python web app deployed on Apache2 that provides an intuitive touch-friendly interface to play various goal horn sounds and activate synchronized LED strobing lights. Perfect for celebrating Blues goals in real-time or practice mode.

**Current Version:** v2.0.0

## Features

- **Multiple Goal Horn Sounds**: Play different goal horn variations including:
  - Power Play
  - Winter Classic
  - Old School
  - Marching In (regular and Glenn variation)

- **LED Strobing Effects**: Synchronized LED light strobing via GPIO pins with active-low relay support
- **Volume Control**: Adjust audio playback volume up/down on the fly with real-time display
- **Audio Status Indicator**: Visual indicator showing whether audio is currently playing
- **Stop Button**: Immediately stop any playing audio
- **Smart Action Locking**: Prevents multiple simultaneous button triggers for 35 seconds
- **Activity Logging**: Complete history of all actions with timestamps
- **Real-Time Status API**: Get current volume and system state via JSON endpoint
- **Responsive Mobile-First UI**: Modern web interface optimized for tablets and mobile devices
- **Visual Feedback**: Button press effects, notifications, and status updates
- **Easy-to-Use Web Interface**: Simple button grid for quick access to all functions

## Hardware Requirements

- **Raspberry Pi** (tested on RPi 2B+, 3B+, 4B)
- **LED Strobing Lights** (connected to GPIO pins 7 and 8)
- **Audio Output** (3.5mm jack or USB audio device)
- **Network Connection** (for web access)

## Software Requirements

### System Packages

```bash
sudo apt-get install python3 python3-pip git apache2 mpg321 php
sudo apt install python3-rpi.gpio
```

> **Note:** PHP is included to support Apache2 server. `python3-rpi.gpio` is essential for GPIO instructions to be properly passed to the lights for controlling on/off states.

### Python Dependencies

```bash
sudo pip3 install alsaaudio
```

## Installation & Setup

### 1. Clone the Repository

```bash
cd /var/www/html
sudo git clone https://github.com/jpk300/bluesgoal.git
cd bluesgoal
git checkout v2.0.0
```

### 2. Configure Apache2

Ensure your web root is configured to serve from `/var/www/html/`:

```bash
# Start Apache2
sudo systemctl start apache2

# Enable on boot
sudo systemctl enable apache2

# Check status
sudo systemctl status apache2
```

### 3. Create Log Directory

```bash
# Create logs directory for activity tracking
sudo mkdir -p /var/www/html/logs
sudo chown www-data:www-data /var/www/html/logs
sudo chmod 755 /var/www/html/logs
```

### 4. Add MP3 Files

Create the `mp3` directory and add your goal horn audio files:

```bash
mkdir -p /var/www/html/mp3

# Add these files (replace with your audio):
# - powerplay.mp3
# - bluesgoal_winterclassic.mp3
# - bluesgoal_oldschool.mp3
# - marching_in.mp3
# - marching_in_glenn.mp3
```

### 5. Configure Sudo Permissions

The PHP scripts execute Python scripts with `sudo`. To avoid password prompts, add this to sudoers:

```bash
sudo visudo
```

Add these lines at the end:

```
www-data ALL=(ALL) NOPASSWD: /usr/bin/python
www-data ALL=(ALL) NOPASSWD: /usr/bin/python3
```

### 6. Set File Permissions

```bash
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html/goalhorn
sudo chmod +x /var/www/html/*.py
```

## Usage

Access the web interface through a browser:

```
http://bluesgoal.home.local
```

Or use the Raspberry Pi's IP address:

```
http://<raspberry-pi-ip>
```

### Control Buttons

- **Goal Horn Variations**: Click any goal horn button to play that sound and trigger LED strobe
- **Volume Down/Up**: Adjust audio levels by 5dB increments (shows real-time volume %)
- **Stop**: Immediately halt any playing audio
- **Status Indicator**: Green dot shows audio is playing, gray shows idle

### Real-Time Status API

Get current system state as JSON:

```bash
curl http://bluesgoal.home.local/goalhorn/_status.php
```

Returns:
```json
{
  "success": true,
  "data": {
    "volume": 85,
    "audio_playing": false,
    "recent_actions": [...],
    "activity_summary": {"powerplay": 5, "stop": 4}
  }
}
```

## Project Structure

```
bluesgoal/
├── README.md
├── config.py                  # Centralized configuration
├── logger.py                  # Logging module for activity tracking
├── log_activity.py            # PHP bridge for logging
├── .gitignore                 # Git ignore configuration
├── index.html                 # Main web interface with enhanced UX
├── stylesheets/
│   └── main.css              # Responsive CSS styling (mobile-optimized)
├── goalhorn/
│   ├── _bluesgoal_*.php      # Endpoint scripts for sound triggers
│   ├── _stop.php             # Stop playback endpoint (JSON response)
│   ├── _status.php           # System status endpoint
│   ├── _volume_*.php         # Volume control endpoints
│   ├── helpers/
│   │   └── endpoint_helper.php  # Shared PHP utilities
│   ├── bluesgoal_oldschool/   # Old school goal horn scripts
│   ├── bluesgoal_winterclassic/
│   ├── marching_in/
│   ├── marching_in_glenn/
│   ├── powerplay/
│   ├── status/
│   │   └── status.py         # Backend for status endpoint
│   ├── stop/                 # Stop/kill audio process
│   ├── volume/               # Volume control scripts
│   └── unused/               # Deprecated scripts
├── images/                   # Button images and backgrounds
├── mp3/                      # Goal horn audio files (not in repo)
├── logs/                     # Activity history (created at setup)
│   └── history.log          # JSON-formatted activity log
├── testscripts/              # GPIO and audio testing utilities
│   ├── test_gpio_alternating.py
│   ├── test_gpio_simultaneous.py
│   └── test_music.py
└── index_backups/            # Previous index.html versions
```

## How It Works

1. **User clicks a button** on the web interface
2. **JavaScript prevents page reload** and makes a fetch request to the PHP endpoint
3. **Action lock check** - Verifies no similar action is already in progress (35 second timeout)
4. **PHP endpoint executes** the corresponding Python script with `sudo`
5. **Activity logging** - Action is logged to `/var/www/html/logs/history.log`
6. **Python script runs**:
   - For audio: Sets GPIO pins to OUTPUT (HIGH) mode, plays MP3 file, waits 30 seconds, sets GPIO to INPUT (HIGH) mode
   - For stop: Kills any active audio process
   - For volume: Adjusts ALSA mixer levels
7. **JSON response** is sent back with success status and message
8. **Frontend updates**: Shows notification and refreshes status from API
9. **LEDs strobe** in sync with the audio playback

## GPIO Pin Usage

- **Pin 7**: LED strobe control (active-low relay)
- **Pin 8**: LED strobe control (active-low relay)

Both pins use **active-low logic**:
- **HIGH (3.3V)** = Relay OFF (lights off)
- **LOW (0V)** = Relay ON (lights on/strobing)

**Important**: The `python3-rpi.gpio` package must be installed for GPIO instructions to be properly passed to the lights:

```bash
sudo apt install python3-rpi.gpio
```

## Logging & Activity History

All button clicks and actions are logged to JSON format for easy tracking:

```bash
# View real-time activity log
tail -f /var/www/html/logs/history.log

# Count actions by type
cat /var/www/html/logs/history.log | jq '.action' | sort | uniq -c

# Pretty-print the log
cat /var/www/html/logs/history.log | jq '.'
```

Sample log entry:
```json
{
  "timestamp": "2026-05-23 14:44:38",
  "action": "powerplay",
  "message": "Triggered from web UI",
  "source": "web_ui"
}
```

## Configuration

Edit `config.py` to customize:

```python
# Paths
BASE_PATH = '/var/www/html'
MP3_DIR = '/var/www/html/mp3'
LOG_DIR = '/var/www/html/logs'

# GPIO Settings
RELAY_PINS = [7, 8]
RELAY_ACTIVE_LOW = True      # HIGH=OFF, LOW=ON
RELAY_DURATION = 30           # seconds

# Audio Settings
AUDIO_CARD = 1                # ALSA card number
VOLUME_STEP = '5dB'           # Volume increment

# Sound Mappings
SOUNDS = {
    'powerplay': 'powerplay.mp3',
    'bluesgoal_winterclassic': 'bluesgoal_winterclassic.mp3',
    # ... more sounds
}
```

## Testing

The project includes test scripts to verify GPIO and audio functionality:

```bash
# Test alternating GPIO pattern (pins 7 and 8 alternate)
sudo python3 testscripts/test_gpio_alternating.py

# Test simultaneous GPIO pattern (pins 7 and 8 trigger together)
sudo python3 testscripts/test_gpio_simultaneous.py

# Test audio playback with all MP3 files
python3 testscripts/test_music.py
```

## Troubleshooting

### Audio Not Playing

- Verify MP3 files exist in `/var/www/html/mp3/`
- Check that `mpg321` is installed: `which mpg321`
- Test manual playback: `mpg321 /var/www/html/mp3/powerplay.mp3`
- Check audio output device is configured correctly
- Use test script: `python3 testscripts/test_music.py`

### LEDs Not Strobing

- Verify GPIO pins 7 & 8 are properly wired
- Check that `python3-rpi.gpio` is installed: `dpkg -l | grep rpi.gpio`
- Reinstall if needed: `sudo apt install python3-rpi.gpio`
- Test GPIO manually: `python3 -c "import RPi.GPIO as GPIO; print(GPIO.VERSION)"`
- Use test scripts to verify GPIO patterns: `sudo python3 testscripts/test_gpio_alternating.py`
- Ensure the script runs with proper permissions (verify sudoers config)
- Verify GPIO pins are not already in use by another process
- Check relay wiring for active-low logic (HIGH = OFF, LOW = ON)

### Page Not Loading

- Verify Apache2 is running: `sudo systemctl status apache2`
- Check file permissions: `ls -la /var/www/html`
- Review Apache error log: `sudo tail -f /var/log/apache2/error.log`

### Volume Control Not Working

- Verify `alsaaudio` is installed: `pip3 list | grep alsaaudio`
- Check ALSA mixer setup: `alsamixer`
- Verify correct audio card: `arecord -l` or `cat /proc/asound/cards`
- Test volume control manually: `amixer -c 1 set PCM 5dB+`

### NHL Feed Polling Errors

When the settings page shows `Waiting for worker status`, `Starting worker`, or `Worker unavailable`, check these in order:

```bash
# 1. Read the feed endpoint exactly as the browser sees it.
curl -s http://bluesgoal.home.local/goalhorn/_nhl_feed.php | jq .

# 2. Inspect the worker status file written by PHP and the Python worker.
sudo cat /tmp/bluesgoal_nhl_feed_status.json | jq .

# 3. Confirm whether the feed is enabled. A value of 1 means enabled.
sudo cat /tmp/bluesgoal_nhl_feed_enabled

# 4. Confirm whether the worker process is running.
pgrep -af 'goalhorn/nhl_feed/nhl_feed.py'

# 5. Watch worker startup stderr/stdout captured from nohup.
sudo tail -f /tmp/bluesgoal_nhl_feed.log

# 6. Watch NHL-specific activity entries such as nhl_api_error and nhl_api_goal.
sudo tail -f /var/www/html/logs/history.log

# 7. Watch app-level logger errors.
sudo tail -f /var/www/html/logs/error.log

# 8. Check Apache/PHP errors if the endpoint itself is failing.
sudo tail -f /var/log/apache2/error.log
```

The most useful fields in `/tmp/bluesgoal_nhl_feed_status.json` are `message`, `last_error`, `running`, `source_team`, `mode`, `last_schedule_check_at`, `last_poll_at`, `current_poll_seconds`, `game_today`, `triggers_expected`, and `watched_game_id`. If `last_error` mentions sudo or a password prompt, confirm the Apache user can launch Python without interaction:

```bash
sudo -u www-data sudo -n python3 -c 'print("sudo ok")'
```

If that fails, revisit the sudoers setup and make sure `www-data` has passwordless access to `/usr/bin/python3`. After fixing sudoers, toggle the NHL API feed off and back on, or request the status endpoint again, to trigger a worker restart.

### Status API Returns "unknown" Volume

- Check ALSA mixer is configured: `amixer -c 1 get PCM`
- Ensure card number matches config.py: `cat /proc/asound/cards`

### Action Lock / "Wait for current action to complete"

- This is expected behavior to prevent simultaneous triggers
- Lock timeout is 35 seconds (configurable in config.py)
- Check activity log to see what action is running

## Recent Updates (v2.0.0 - Latest)

- ✅ **Fixed PHP redirect bug** - Now returns JSON responses instead of redirecting
- ✅ **Python 3 migration** - All scripts updated to use Python 3
- ✅ **Comprehensive error handling** - Try/catch blocks and proper error messages
- ✅ **Real-time volume display** - Shows current volume % from ALSA mixer
- ✅ **Smart action locking** - Prevents simultaneous button triggers
- ✅ **Enhanced UX** - Button feedback, notifications, audio status indicator
- ✅ **Activity logging** - Complete history with JSON format for easy parsing
- ✅ **Config module** - Centralized configuration for easy customization
- ✅ **Status API** - JSON endpoint for real-time system state
- ✅ **Updated mobile view** - Improved responsive design and viewport optimization
- ✅ **Updated button styling** - Ovals with white background for volume/stop controls

## Future Enhancements

- Add NHL API integration to automatically trigger on Blues goals
- Support for additional audio formats (OGG, WAV)
- Customizable strobe patterns and durations
- Web-based audio file uploader
- Mobile app for remote control
- Statistics dashboard showing most-played sounds
- Scheduled/timed triggers
- Multiple zone support (separate light controls)

## License

Personal project - feel free to adapt for your own use!

## Notes

- Default localhost name: `bluesgoal.home.local` (configure in your network DNS or `/etc/hosts`)
- The app requires `www-data` (Apache user) to have sudoers permissions to run Python scripts
- LED strobing uses active-low relay logic (configure in config.py if needed)
- All audio playback uses `mpg321` command-line utility
- GPIO control requires `python3-rpi.gpio` system package for proper hardware communication
- Images and audio files are excluded from git (see `.gitignore`)
- Activity logs are stored as JSON for easy programmatic access

# St. Louis Blues Goal Horn Web App

**Last updated:** May 29, 2026  
**Current Version:** v2.1.0

A web-based goal horn and celebration system running on a Raspberry Pi that plays music and triggers LED strobing effects when the St. Louis Blues score a goal. Features both manual button control and automatic NHL API integration.

## Overview

This application is a Python/PHP web app deployed on Apache2 that provides an intuitive touch-friendly interface to play various goal horn sounds, activate synchronized LED strobing lights, and optionally monitor the NHL API for automatic goal detection. Perfect for Blues fans who want an interactive celebration experience.

**Language Composition:**
- Python (50.8%) - Backend audio/GPIO control
- HTML (24.1%) - Web interface markup
- PHP (14.2%) - Apache endpoints and integrations
- CSS (10.9%) - Responsive styling

## Quick Start

```bash
# Clone to Apache web root
cd /var/www/html
sudo git clone https://github.com/jpk300/bluesgoal.git
cd bluesgoal
git checkout v2.1.0

# Install dependencies
sudo apt-get install python3 python3-pip apache2 mpg321 php python3-rpi.gpio
sudo pip3 install alsaaudio

# Create writable app directories
sudo mkdir -p /var/www/html/logs /var/www/html/runtime
sudo chown -R www-data:www-data /var/www/html/logs /var/www/html/runtime
sudo chmod 775 /var/www/html/logs /var/www/html/runtime

# Access the app
http://bluesgoal.home.local
```

## Features

### Audio & Strobe Control
- **5 Goal Horn Variations**: Power Play, Winter Classic, Old School, Marching In, Marching In (Glenn)
- **LED Strobing Effects**: Synchronized LED strobing via GPIO pins (pins 7 & 8) with active-low relay support
- **Stop Button**: Immediately halt any playing audio
- **Volume Control**: Adjust playback volume up/down in 5dB increments with real-time display

### User Experience
- **Responsive Mobile-First UI**: Touch-optimized for tablets and mobile devices
- **Visual Feedback**: Button press effects, notifications, and status updates
- **Audio Status Indicator**: Real-time indicator showing whether audio is currently playing
- **Activity Logging**: Complete JSON-formatted history of all button actions with timestamps

### Smart Features
- **Action Locking**: Prevents multiple simultaneous button triggers for 35 seconds (prevents overlapping audio)
- **Real-Time Status API**: Get current volume, audio status, and system state via JSON endpoint
- **NHL API Integration**: Automatic goal detection and horn triggering for Blues games (optional, configurable)
- **Settings Page**: Web-based configuration for NHL team selection and feed control

## Hardware Requirements

- **Raspberry Pi** (tested on RPi 2B+, 3B+, 4B)
- **LED Strobing Lights** (connected to GPIO pins 7 and 8)
- **Audio Output** (3.5mm jack or USB audio device)
- **Network Connection** (for web access and optional NHL API polling)

## Software Requirements

### System Packages

```bash
sudo apt-get install python3 python3-pip git apache2 mpg321 php python3-rpi.gpio
```

> **Important:** `python3-rpi.gpio` is essential for GPIO pin control. Without it, relay instructions won't be properly passed to the LED lights.

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
git checkout v2.1.0
```

### 2. Configure Apache2

Ensure Apache2 is running and your web root is `/var/www/html/`:

```bash
# Start Apache2
sudo systemctl start apache2

# Enable on boot
sudo systemctl enable apache2

# Check status
sudo systemctl status apache2
```

### 3. Create Writable App Directories

```bash
# Create logs and persistent runtime state directories
sudo mkdir -p /var/www/html/logs /var/www/html/runtime
sudo chown -R www-data:www-data /var/www/html/logs /var/www/html/runtime
sudo chmod 775 /var/www/html/logs /var/www/html/runtime
```

### 4. Add MP3 Audio Files

Create the `mp3` directory and add your goal horn audio files:

```bash
mkdir -p /var/www/html/mp3

# Required files (or customize via config.py):
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
sudo chown -R www-data:www-data /var/www/html/bluesgoal
sudo chmod -R 755 /var/www/html/bluesgoal
sudo chmod +x /var/www/html/bluesgoal/*.py
```

## Usage

### Accessing the Web Interface

Via mDNS hostname (recommended, requires network configuration):
```
http://bluesgoal.home.local
```

Or use the Raspberry Pi's IP address:
```
http://<raspberry-pi-ip>
```

### Main Interface (index.html)

- **Goal Horn Buttons**: Click any button to play that sound and trigger LED strobe (5 variations arranged in grid)
- **Volume Controls**: Adjust audio by 5dB increments (displays real-time volume %)
- **Stop Button**: Immediately halt playback
- **Audio Indicator**: Green dot shows audio is playing, gray shows idle
- **Settings Link**: Access NHL API and other configuration options (top-right corner)

### Settings Page (settings.html)

Configure NHL API integration:
- **Enable/Disable NHL API Feed**: Toggle automatic goal detection
- **Select Source Team**: Choose which NHL team to monitor (default: St. Louis Blues)
- **Feed Status**: View current worker process status and recent activity

## Project Structure

```
bluesgoal/
├── README.md                  # This file
├── config.py                  # Centralized configuration settings
├── logger.py                  # Logging module for activity tracking
├── log_activity.py            # PHP bridge for logging
├── index.html                 # Main web interface
├── settings.html              # NHL API configuration page
├── .gitignore                 # Git ignore configuration
│
├── stylesheets/
│   └── main.css              # Responsive CSS styling (mobile-optimized)
│
├── images/                   # Button images and backgrounds
│
├── goalhorn/                 # Apache endpoints and backend scripts
│   ├── _powerplay.php        # Power Play endpoint
│   ├── _bluesgoal_winterclassic.php
│   ├── _bluesgoal_oldschool.php
│   ├── _marching_in.php
│   ├── _marching_in_glenn.php
│   ├── _stop.php             # Stop playback endpoint
│   ├── _status.php           # System status JSON endpoint
│   ├── _volume_up.php        # Volume control endpoints
│   ├── _volume_down.php
│   ├── _nhl_feed.php         # NHL API feed control endpoint
│   ├── _helpers.php          # Shared PHP utilities and logging
│   │
│   ├── powerplay/            # Backend Python scripts for each action
│   ├── bluesgoal_oldschool/
│   ├── bluesgoal_winterclassic/
│   ├── marching_in/
│   ├── marching_in_glenn/
│   ├── status/
│   ├── stop/                 # Kill audio process
│   ├── volume/               # Volume control Python scripts
│   ├── nhl_feed/             # NHL API worker and integrations
│   │   └── nhl_feed.py       # Background worker for goal detection
│   │
│   └── unused/               # Deprecated scripts
│
├── mp3/                      # Goal horn audio files (not in git)
├── logs/                     # Activity history (created at setup)
│   ├── history.log          # JSON-formatted activity log
│   └── error.log            # Application errors
│
├── runtime/                  # Persistent NHL feed state, locks, and worker logs
│
└── testscripts/              # Testing utilities
    ├── test_gpio_alternating.py   # Test alternating GPIO pattern
    ├── test_gpio_simultaneous.py  # Test simultaneous GPIO pattern
    └── test_music.py              # Test audio playback
```

## How It Works

### Manual Button Flow

1. **User clicks a button** on the web interface (index.html)
2. **JavaScript prevents page reload** and makes a fetch request to the PHP endpoint
3. **Action lock check** - Verifies no similar action is already in progress (35 second timeout)
4. **PHP endpoint executes** the corresponding Python script with `sudo`
5. **Activity logging** - Action is logged to `/var/www/html/logs/history.log`
6. **Python script runs**:
   - For audio: Sets GPIO pins to OUTPUT (HIGH) mode, plays MP3 via mpg321, waits for completion, sets GPIO to INPUT (HIGH) mode
   - For stop: Kills any active audio process
   - For volume: Adjusts ALSA mixer levels
7. **JSON response** is sent back with success status and message
8. **Frontend updates**: Shows notification and refreshes status from API
9. **LEDs strobe** in sync with audio playback

### NHL API Integration (Optional)

When enabled, a background Python worker continuously polls the NHL API:

1. **Worker starts** via `nhl_feed.php` endpoint
2. **Polls NHL API** for Blues game status and goal events
3. **Automatically triggers** goal horn when goal is detected
4. **Logs events** to activity history
5. **Reports status** via `/var/www/html/runtime/nhl_feed_status.json`

## Configuration

Edit `config.py` to customize the application:

```python
# Paths
BASE_PATH = '/var/www/html'
MP3_DIR = '/var/www/html/mp3'
LOG_DIR = '/var/www/html/logs'
RUNTIME_DIR = '/var/www/html/runtime'

# GPIO Settings
GPIO_MODE = 'BOARD'           # Pin numbering mode
RELAY_PINS = [7, 8]           # GPIO pins for LED control
RELAY_ACTIVE_LOW = True        # HIGH=OFF, LOW=ON
RELAY_DURATION = 30            # Strobe duration in seconds

# Audio Settings
AUDIO_CARD = 1                 # ALSA card number
VOLUME_STEP = '5dB'            # Volume increment
AUDIO_PLAYER = 'mpg321'        # Audio player command

# Sound Mappings
SOUNDS = {
    'powerplay': 'powerplay.mp3',
    'bluesgoal_winterclassic': 'bluesgoal_winterclassic.mp3',
    'bluesgoal_oldschool': 'bluesgoal_oldschool.mp3',
    'marching_in': 'marching_in.mp3',
    'marching_in_glenn': 'marching_in_glenn.mp3',
}

# Logging
LOG_LEVEL = 'INFO'             # DEBUG, INFO, WARNING, ERROR
```

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
  "timestamp": "2026-05-29 14:44:38",
  "action": "powerplay",
  "message": "Triggered from web UI",
  "source": "web_ui"
}
```

Sample NHL API log entry:
```json
{
  "timestamp": "2026-05-29 15:22:15",
  "action": "nhl_api_goal",
  "message": "Goal detected for St. Louis Blues",
  "source": "nhl_worker"
}
```

## API Endpoints

### Real-Time Status API

Get current system state as JSON:

```bash
curl http://bluesgoal.home.local/goalhorn/_status.php
```

Response:
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

### NHL Feed API

Get NHL feed status and configuration:

```bash
curl http://bluesgoal.home.local/goalhorn/_nhl_feed.php
```

Response:
```json
{
  "success": true,
  "enabled": true,
  "running": true,
  "settings": {
    "source_team": "STL"
  },
  "teams": ["ANA", "BOS", "BUF", ...],
  "message": "NHL API feed enabled",
  "data": {
    "running": true,
    "message": "Polling for Blues goals",
    "last_poll_at": "2026-05-29T20:15:30Z"
  }
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
- Verify audio output device is configured correctly
- Use test script: `python3 testscripts/test_music.py`
- Check that audio card number matches `config.py` (`AUDIO_CARD`)

### LEDs Not Strobing

- Verify GPIO pins 7 & 8 are properly wired to relay switches
- Check that `python3-rpi.gpio` is installed: `dpkg -l | grep rpi.gpio`
- Reinstall if needed: `sudo apt install python3-rpi.gpio`
- Test GPIO manually: `python3 -c "import RPi.GPIO as GPIO; print(GPIO.VERSION)"`
- Use test scripts to verify GPIO patterns: `sudo python3 testscripts/test_gpio_alternating.py`
- Ensure the script runs with proper permissions (verify sudoers config)
- Verify GPIO pins are not already in use by another process
- Check relay wiring for active-low logic (HIGH = OFF, LOW = ON)

### Page Not Loading

- Verify Apache2 is running: `sudo systemctl status apache2`
- Check file permissions: `ls -la /var/www/html/bluesgoal`
- Review Apache error log: `sudo tail -f /var/log/apache2/error.log`
- Verify the repository path matches Apache DocumentRoot

### Volume Control Not Working

- Verify `alsaaudio` is installed: `pip3 list | grep alsaaudio`
- Check ALSA mixer setup: `alsamixer`
- Verify correct audio card: `arecord -l` or `cat /proc/asound/cards`
- Test volume control manually: `amixer -c 1 set PCM 5dB+`
- Ensure `config.py` has the correct `AUDIO_CARD` number

### Status API Returns "unknown" Volume

- Check ALSA mixer is configured: `amixer -c 1 get PCM`
- Ensure card number matches `config.py`: `cat /proc/asound/cards`

### Action Lock / "Wait for current action to complete"

- This is expected behavior to prevent simultaneous triggers
- Lock timeout is 35 seconds (configurable in `config.py`)
- Check activity log to see what action is running: `tail -f /var/www/html/logs/history.log`

### NHL Feed Polling Errors

When the settings page shows `Waiting for worker status`, `Starting worker`, or `Worker unavailable`, check these in order:

```bash
# 1. Read the feed endpoint status
curl -s http://bluesgoal.home.local/goalhorn/_nhl_feed.php | jq .

# 2. Inspect the worker status file
sudo cat /var/www/html/runtime/nhl_feed_status.json | jq .

# 3. Verify the feed is enabled (1 = enabled)
sudo cat /var/www/html/runtime/nhl_feed_enabled

# 4. Confirm the worker process is running
pgrep -af 'goalhorn/nhl_feed/nhl_feed.py'

# 5. Watch worker startup logs
sudo tail -f /var/www/html/runtime/nhl_feed.log

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

**Note on systemd PrivateTmp**: NHL feed state is stored in `/var/www/html/runtime`, not `/tmp`, so Apache `PrivateTmp` isolation should not hide the worker status or logs.

The most reliable status check is always:
```bash
curl -s http://localhost/goalhorn/_nhl_feed.php | jq .
```

## Recent Updates

### v2.1.0 (Latest)
- ✅ **NHL API Integration** - Automatic goal detection and horn triggering for Blues games
- ✅ **Settings Page** - Web-based configuration for NHL team selection and feed control
- ✅ **Background Worker** - Dedicated Python process for polling NHL API
- ✅ **Worker Status Monitoring** - Real-time display of NHL feed status
- ✅ **Enhanced Activity Logging** - Separate tracking for NHL API events
- ✅ **Better Error Messaging** - Comprehensive troubleshooting information

### v2.0.0
- ✅ **Fixed PHP redirect bug** - Now returns JSON responses instead of redirecting
- ✅ **Python 3 migration** - All scripts updated to use Python 3
- ✅ **Comprehensive error handling** - Try/catch blocks and proper error messages
- ✅ **Real-time volume display** - Shows current volume % from ALSA mixer
- ✅ **Smart action locking** - Prevents simultaneous button triggers
- ✅ **Enhanced UX** - Button feedback, notifications, audio status indicator
- ✅ **Activity logging** - Complete history with JSON format for easy parsing
- ✅ **Config module** - Centralized configuration for easy customization
- ✅ **Status API** - JSON endpoint for real-time system state
- ✅ **Responsive design** - Improved mobile view and viewport optimization

## Future Enhancements

- Web-based audio file uploader
- Mobile app for remote control
- Statistics dashboard showing most-played sounds


## Notes

- Default localhost name: `bluesgoal.home.local` (configure in your network DNS or `/etc/hosts`)
- The app requires `www-data` (Apache user) to have sudoers permissions to run Python scripts
- LED strobing uses active-low relay logic (configure in `config.py` if needed)
- All audio playback uses the `mpg321` command-line utility
- GPIO control requires `python3-rpi.gpio` system package for proper hardware communication
- Images and audio files are excluded from git (see `.gitignore`)
- Activity logs are stored as JSON for easy programmatic access
- NHL API worker runs as a separate background process managed by PHP

## License

Personal project - feel free to adapt for your own use!

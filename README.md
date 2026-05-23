# St. Louis Blues Goal Horn Web App

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

- **LED Strobing Effects**: Synchronized LED light strobing via GPIO pins with alternating and simultaneous patterns
- **Volume Control**: Adjust audio playback volume up/down on the fly
- **Stop Button**: Immediately stop any playing audio
- **Responsive Mobile-First UI**: Modern web interface optimized for tablets and mobile devices with improved mobile viewport
- **Easy-to-Use Web Interface**: Simple button grid for quick access to all functions

## Hardware Requirements

- **Raspberry Pi** (tested on RPi 2b)
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

### 3. Add MP3 Files

Create the `mp3` directory and add your goal horn audio files:

```bash
mkdir -p /var/www/html/mp3

# Add these files (replace with your audio):
# - bluesgoal_powerplay.mp3
# - bluesgoal_winterclassic.mp3
# - bluesgoal_oldschool.mp3
# - marching_in.mp3
# - marching_in_glenn.mp3
```

### 4. Configure Sudo Permissions

The PHP scripts execute Python scripts with `sudo`. To avoid password prompts, add this to sudoers:

```bash
sudo visudo
```

Add these lines at the end:

```
www-data ALL=(ALL) NOPASSWD: /usr/bin/python
www-data ALL=(ALL) NOPASSWD: /usr/bin/python3
```

### 5. Set File Permissions

```bash
sudo chown -R www-data:www-data /var/www/html
sudo chmod -R 755 /var/www/html/goalhorn
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
- **Volume Down/Up**: Adjust audio levels by ±5% increments
- **Stop**: Immediately halt any playing audio

## Project Structure

```
bluesgoal/
├── README.md
├── .gitignore                 # Git ignore configuration
├── index.html                 # Main web interface
├── stylesheets/
│   └── main.css              # Responsive CSS styling (mobile-optimized)
├── goalhorn/
│   ├── _bluesgoal_*.php      # Endpoint scripts for sound triggers
│   ├── _stop.php             # Stop playback endpoint
│   ├── _volume_*.php         # Volume control endpoints
│   ├── bluesgoal_oldschool/   # Old school goal horn scripts
│   ├── bluesgoal_winterclassic/
│   ├── marching_in/
│   ├── marching_in_glenn/
│   ├── powerplay/
│   ├── stop/                 # Stop/kill audio process
│   ├── volume/               # Volume control scripts
│   └── unused/               # Deprecated scripts
├── images/                   # Button images and backgrounds
├── mp3/                      # Goal horn audio files (not in repo)
├── testscripts/              # GPIO and audio testing utilities
│   ├── test_gpio_alternating.py
│   ├── test_gpio_simultaneous.py
│   └── test_music.py
└── index_backups/            # Previous index.html versions
```

## How It Works

1. **User clicks a button** on the web interface
2. **JavaScript prevents page reload** and makes a fetch request to the appropriate PHP endpoint
3. **PHP script executes** the corresponding Python master script with `sudo`
4. **Python master script**:
   - Sets GPIO pins 7 & 8 to input mode initially
   - Spawns the audio/action Python subprocess
   - Sets GPIO pins to output mode (strobing LEDs)
   - Cleans up GPIO after completion
5. **Audio subprocess** plays the MP3 file or performs the requested action
6. **LEDs strobe** in sync with the audio playback

## GPIO Pin Usage

- **Pin 7**: LED strobe control
- **Pin 8**: LED strobe control

Both pins are set to OUTPUT mode during the celebration sequence, triggering your LED strobing hardware.

**Important**: The `python3-rpi.gpio` package must be installed for GPIO instructions to be properly passed to the lights for turning them on/off:

```bash
sudo apt install python3-rpi.gpio
```

This package provides the necessary system-level GPIO control that allows the Python RPi.GPIO library to communicate with the Raspberry Pi's GPIO pins.

## Testing

The project includes test scripts to verify GPIO and audio functionality:

```bash
# Test alternating GPIO pattern (pins 7 and 8 alternate)
sudo python3 testscripts/test_gpio_alternating.py

# Test simultaneous GPIO pattern (pins 7 and 8 trigger together)
sudo python3 testscripts/test_gpio_simultaneous.py

# Test audio playback
python3 testscripts/test_music.py
```

## Troubleshooting

### Audio Not Playing

- Verify MP3 files exist in `/var/www/html/mp3/`
- Check that `mpg321` is installed: `which mpg321`
- Test manual playback: `mpg321 /var/www/html/mp3/gloria.mp3`
- Check audio output device is configured correctly
- Use test script: `python3 testscripts/test_music.py`

### LEDs Not Strobing

- Verify GPIO pins 7 & 8 are properly wired
- Check that `python3-rpi.gpio` is installed: `dpkg -l | grep rpi.gpio`
- Reinstall if needed: `sudo apt install python3-rpi.gpio`
- Test GPIO manually: `python3 -c "import RPi.GPIO as GPIO; print(GPIO.VERSION)"`
- Use test scripts to verify GPIO patterns: `sudo python3 testscripts/test_gpio_alternating.py`
- Ensure the script runs with proper permissions (sudo via sudoers config)
- Verify GPIO pins are not already in use by another process

### Page Not Loading

- Verify Apache2 is running: `sudo systemctl status apache2`
- Check file permissions: `ls -la /var/www/html`
- Review Apache error log: `sudo tail -f /var/log/apache2/error.log`

### Volume Control Not Working

- Verify `alsaaudio` is installed: `pip3 list | grep alsaaudio`
- Check ALSA mixer setup: `alsamixer`

## Recent Updates (v2.0.0)

- **Rewrote PHP scripts** for improved reliability and light control
- **Resolved light control issues** with proper GPIO handling
- **Updated mobile view** with improved responsive design and viewport optimization
- **Sound configuration updates** for better audio playback
- **Added test scripts** for GPIO and audio debugging

## Future Enhancements

- Add NHL API integration to automatically trigger on Blues goals
- Support for additional audio formats (OGG, WAV)
- Customizable strobe patterns and durations
- Web-based audio file uploader
- Statistics/logging of celebrations
- Mobile app for remote control

## License

Personal project - feel free to adapt for your own use!

## Notes

- Default localhost name: `bluesgoal.home.local` (configure in your network DNS or `/etc/hosts`)
- The app requires `www-data` (Apache user) to have sudoers permissions to run Python scripts
- LED strobing patterns can be tested independently using test scripts
- All audio playback uses `mpg321` command-line utility
- GPIO control requires `python3-rpi.gpio` system package for proper hardware communication
- Images and audio files are excluded from git (see `.gitignore`)

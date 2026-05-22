# St. Louis Blues Goal Horn Web App

A web-based goal horn and celebration system running on a Raspberry Pi that plays music and triggers LED strobing effects when the St. Louis Blues score a goal.

## Overview

This application is a Python web app deployed on Apache2 that provides an intuitive touch-friendly interface to play various goal horn sounds and activate synchronized LED strobing lights. Perfect for Blues fans who want a dedicated celebration system!

**Current Version:** v2.0.0

## Features

- **Multiple Goal Horn Sounds**: Play different goal horn variations including:
  - 2019 Playoffs
  - Winter Classic
  - Old School
  - Current Season
  - Gloria
  - Marching In (regular and Glenn variation)
  - Power Play

- **LED Strobing Effects**: Synchronized LED light strobing via GPIO pins (30-second sequences)
- **Volume Control**: Adjust audio playback volume up/down on the fly
- **Stop Button**: Immediately stop any playing audio
- **Responsive Touch-Friendly UI**: Modern web interface optimized for tablets and touch screens
- **Easy-to-Use Web Interface**: Simple button grid for quick access to all functions

## Hardware Requirements

- **Raspberry Pi** (tested on RPi 3B+ and later)
- **LED Strobing Lights** (connected to GPIO pins 7 and 8)
- **Audio Output** (3.5mm jack or USB audio device)
- **Network Connection** (for web access)

## Software Requirements

### System Packages

```bash
sudo apt-get install python3 python3-pip git apache2 mpg321 php
```

> **Note:** PHP is required if you want to test the scripts from the command line.

### Python Dependencies

```bash
sudo pip3 install RPi.GPIO alsaaudio
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
# - bluesgoal_oldschool.mp3
# - bluesgoal_winterclassic.mp3
# - bluesgoal_current.mp3
# - gloria.mp3
# - (and others as needed)
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
├── index.html                 # Main web interface
├── stylesheets/
│   └── main.css              # Responsive CSS styling
├── goalhorn/
│   ├── _bluesgoal_*.php      # Endpoint scripts (one per goal horn variation)
│   ├── _stop.php             # Stop playback endpoint
│   ├── _volume_*.php         # Volume control endpoints
│   ├── bluesgoal_oldschool/   # Old school goal horn scripts
│   ├── bluesgoal_winterclassic/
│   ├── bluesgoal_current/
│   ├── gloria/
│   ├── marching_in/
│   ├── marching_in_glenn/
│   ├── powerplay/
│   ├── stop/                 # Stop/kill audio process
│   ├── volume/               # Volume control scripts
│   └── unused/               # Deprecated scripts
├── images/                   # Button images and backgrounds
├── mp3/                      # Goal horn audio files (not in repo)
└── index_backups/            # Previous index.html versions
```

## How It Works

1. **User clicks a button** on the web interface
2. **JavaScript prevents page reload** and makes a fetch request to the appropriate PHP endpoint
3. **PHP script executes** the corresponding Python master script with `sudo`
4. **Python master script**:
   - Sets GPIO pins 7 & 8 to input mode initially
   - Spawns the audio/action Python subprocess
   - Sets GPIO pins to output mode (strobing LEDs for 30 seconds)
   - Cleans up GPIO after completion
5. **Audio subprocess** plays the MP3 file or performs the requested action
6. **LEDs strobe** in sync with the audio playback

## GPIO Pin Usage

- **Pin 7**: LED strobe control
- **Pin 8**: LED strobe control

Both pins are set to OUTPUT mode during the 30-second celebration sequence, triggering your LED strobing hardware.

## Troubleshooting

### Audio Not Playing

- Verify MP3 files exist in `/var/www/html/mp3/`
- Check that `mpg321` is installed: `which mpg321`
- Test manual playback: `mpg321 /var/www/html/mp3/gloria.mp3`
- Check audio output device is configured correctly

### LEDs Not Strobing

- Verify GPIO pins 7 & 8 are properly wired
- Check that `RPi.GPIO` is installed for your Python version
- Test GPIO manually: `python3 -c "import RPi.GPIO as GPIO; print(GPIO.VERSION)"`
- Ensure the script runs with proper permissions (sudo via sudoers config)

### Page Not Loading

- Verify Apache2 is running: `sudo systemctl status apache2`
- Check file permissions: `ls -la /var/www/html`
- Review Apache error log: `sudo tail -f /var/apache2/error.log`

### Volume Control Not Working

- Verify `alsaaudio` is installed: `pip3 list | grep alsaaudio`
- Check ALSA mixer setup: `alsamixer`

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
- LED strobing sequences are fixed at 30 seconds per trigger
- All audio playback uses `mpg321` command-line utility

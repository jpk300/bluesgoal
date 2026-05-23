# Bluesgoal

Scripts and web interface for NHL goal horn functionality.

## Overview

Bluesgoal is a project that provides the tools and interface needed to control and manage NHL goal horn functionality. This repository contains Python scripts, HTML/CSS web interface components, and server-side logic for a complete goal horn system.

## Project Structure

- **Python Scripts** (39.3%) - Core functionality and automation scripts
- **HTML** (32.8%) - Web interface templates and markup
- **PHP** (19.2%) - Backend server-side logic
- **CSS** (8.7%) - Styling for the web interface

## Features

- Goal horn control system
- Web-based user interface
- Python-based automation and scripting
- Server-side processing with PHP

## Tech Stack

- Python
- HTML5
- CSS3
- PHP

## Getting Started

1. Clone this repository
2. Review the Python scripts in the main directory
3. Configure your server environment
4. Deploy the HTML/PHP components to your web server

## Post-Installation Setup

### Required MP3 Files
All goal horn audio files must be placed in the `/mp3/` directory:
- `bluesgoal_current.mp3`
- `bluesgoal_winterclassic.mp3`
- `bluesgoal_oldschool.mp3`
- `marching_in.mp3`
- `marching_in_glenn.mp3`
- `marching_in_playoffs.mp3`
- `powerplay.mp3`

### Required Images

#### Page Banner
Place the NHL goal logo banner at the top of the page:
- `nhl_goal_logo.png` or `.jpeg` - Top banner image

#### Button Images
Button images must be placed in the `/images/` directory:
- `button_bluesgoal_winterclassic.jpeg`
- `button_bluesgoal_oldschool.jpeg`
- `button_powerplay.jpeg`
- `button_marching_in.jpeg`
- `button_marching_in_glenn.jpeg`
- `button_marching_in_playoffs.jpeg`
- `button_volume_down.jpeg`
- `button_volume_up.jpeg`
- `button_stop.png`

#### Center Box Image
A center display image for the main interface:
- `center_box_image.jpeg` - Center box display image

#### Background Image
A rotator background image system is used via: `/images/backgrounds/rotator.php`

## License

No license specified

## Support

For issues or questions, please open an issue in this repository.

---

**Repository Info**
- Created: March 20, 2020
- Primary Language: Python
- Status: Active

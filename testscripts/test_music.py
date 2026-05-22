#!/usr/bin/python3

import os
import subprocess
import time

# Path to your MP3 directory
MUSIC_DIR = "/var/www/html/mp3"

# Find all mp3 files
mp3_files = sorted([
    f for f in os.listdir(MUSIC_DIR)
    if f.endswith(".mp3")
])

if not mp3_files:
    print("No MP3 files found.")
    exit(1)

print(f"Found {len(mp3_files)} MP3 files\n")

for mp3 in mp3_files:

    full_path = os.path.join(MUSIC_DIR, mp3)

    print("=" * 60)
    print(f"Playing: {mp3}")
    print("=" * 60)

    try:
        # Play the file and wait for completion
        subprocess.run([
            "mpg321",
            full_path
        ])

    except Exception as e:
        print(f"Error playing {mp3}: {e}")

    print("\nWaiting 2 seconds before next file...\n")
    time.sleep(2)

print("Finished testing all music files.")

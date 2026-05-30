#!/usr/bin/env bash
# Install BluesGoal system package prerequisites on Raspberry Pi OS/Debian.

set -euo pipefail

PACKAGES=(
  python3
  git
  apache2
  php
  mpg321
  alsa-utils
  python3-rpi.gpio
  rsync
)

if [[ ${EUID} -eq 0 ]]; then
  SUDO=()
else
  SUDO=(sudo)
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "ERROR: apt-get was not found. This installer expects Raspberry Pi OS/Debian." >&2
  exit 1
fi

echo "Installing BluesGoal prerequisites: ${PACKAGES[*]}"
if [[ "${SKIP_APT_UPDATE:-0}" != "1" ]]; then
  "${SUDO[@]}" apt-get update
else
  echo "Skipping apt-get update because SKIP_APT_UPDATE=1"
fi

"${SUDO[@]}" apt-get install -y "${PACKAGES[@]}"

if command -v systemctl >/dev/null 2>&1; then
  echo "Enabling and starting Apache2"
  "${SUDO[@]}" systemctl enable apache2
  "${SUDO[@]}" systemctl start apache2
else
  echo "systemctl not found; skipping Apache2 enable/start"
fi

cat <<'SUMMARY'

Prerequisite installation complete.
Next steps:
  1. Deploy the repo contents to /var/www/html.
  2. Run scripts/setup_permissions.sh to create runtime directories and permissions.
  3. Add your local images and MP3 files.
  4. Configure sudoers for www-data as documented in README.md.
SUMMARY


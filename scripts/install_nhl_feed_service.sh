#!/usr/bin/env bash
# Install a systemd service that starts the NHL feed worker on boot.

set -euo pipefail

DOC_ROOT=${DOC_ROOT:-/var/www/html}
WEB_USER=${WEB_USER:-www-data}
WEB_GROUP=${WEB_GROUP:-www-data}
DATA_DIR=${BLUESGOAL_DATA_DIR:-/var/lib/bluesgoal}
RUN_DIR=${BLUESGOAL_RUN_DIR:-/run/bluesgoal}
WORKER_LOG_DIR=${BLUESGOAL_WORKER_LOG_DIR:-/var/log/bluesgoal}
TIMEZONE=${BLUESGOAL_TIMEZONE:-America/Chicago}
SERVICE_NAME=${BLUESGOAL_NHL_SERVICE_NAME:-bluesgoal-nhl-feed}

if [[ ${EUID} -eq 0 ]]; then
  SUDO=()
else
  SUDO=(sudo)
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "ERROR: systemctl was not found. This installer expects systemd." >&2
  exit 1
fi

SCRIPT_PATH="${DOC_ROOT%/}/goalhorn/nhl_feed/nhl_feed.py"
if [[ ! -f "${SCRIPT_PATH}" ]]; then
  echo "ERROR: NHL feed worker not found at ${SCRIPT_PATH}" >&2
  echo "Set DOC_ROOT=/path/to/bluesgoal before running this script if needed." >&2
  exit 1
fi

"${SUDO[@]}" mkdir -p "${DATA_DIR}" "${RUN_DIR}" "${WORKER_LOG_DIR}"
"${SUDO[@]}" chown "${WEB_USER}:${WEB_GROUP}" "${DATA_DIR}" "${RUN_DIR}" "${WORKER_LOG_DIR}"
"${SUDO[@]}" chmod 775 "${DATA_DIR}" "${RUN_DIR}" "${WORKER_LOG_DIR}"

UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

cat <<UNIT | "${SUDO[@]}" tee "${UNIT_PATH}" >/dev/null
[Unit]
Description=BluesGoal NHL feed worker
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${WEB_USER}
Group=${WEB_GROUP}
Environment=BLUESGOAL_DATA_DIR=${DATA_DIR}
Environment=BLUESGOAL_RUN_DIR=${RUN_DIR}
Environment=BLUESGOAL_WORKER_LOG_DIR=${WORKER_LOG_DIR}
Environment=BLUESGOAL_TIMEZONE=${TIMEZONE}
ExecStart=/usr/bin/python3 -B ${SCRIPT_PATH}
Restart=on-failure
RestartSec=15
StandardOutput=append:${WORKER_LOG_DIR}/nhl_feed.log
StandardError=append:${WORKER_LOG_DIR}/nhl_feed.log

[Install]
WantedBy=multi-user.target
UNIT

"${SUDO[@]}" systemctl daemon-reload
"${SUDO[@]}" systemctl enable "${SERVICE_NAME}.service"
"${SUDO[@]}" systemctl start "${SERVICE_NAME}.service"

cat <<SUMMARY

Installed and started ${SERVICE_NAME}.service.

Useful commands:
  systemctl status ${SERVICE_NAME}.service
  journalctl -u ${SERVICE_NAME}.service -f

The worker exits cleanly when the NHL feed is disabled and runs after reboot
when /var/lib/bluesgoal/nhl_feed_enabled contains 1.
SUMMARY

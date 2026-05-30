#!/usr/bin/env bash
# Create BluesGoal runtime directories and apply recommended ownership/permissions.

set -euo pipefail

DOC_ROOT=${DOC_ROOT:-/var/www/html}
WEB_USER=${WEB_USER:-www-data}
WEB_GROUP=${WEB_GROUP:-www-data}
DATA_DIR=${BLUESGOAL_DATA_DIR:-/var/lib/bluesgoal}
RUN_DIR=${BLUESGOAL_RUN_DIR:-/run/bluesgoal}
WORKER_LOG_DIR=${BLUESGOAL_WORKER_LOG_DIR:-/var/log/bluesgoal}
CREATE_TMPFILES=${CREATE_TMPFILES:-1}

usage() {
  cat <<USAGE
Usage: $0 [--no-tmpfiles]

Environment overrides:
  DOC_ROOT                     Apache document root (default: /var/www/html)
  WEB_USER                     Apache/PHP user (default: www-data)
  WEB_GROUP                    Apache/PHP group (default: www-data)
  BLUESGOAL_DATA_DIR           Durable app state directory (default: /var/lib/bluesgoal)
  BLUESGOAL_RUN_DIR            Runtime lock/status directory (default: /run/bluesgoal)
  BLUESGOAL_WORKER_LOG_DIR     NHL worker log directory (default: /var/log/bluesgoal)
  CREATE_TMPFILES              Write /etc/tmpfiles.d rule when 1 (default: 1)
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-tmpfiles)
      CREATE_TMPFILES=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ${EUID} -eq 0 ]]; then
  SUDO=()
else
  SUDO=(sudo)
fi

if ! id "${WEB_USER}" >/dev/null 2>&1; then
  echo "ERROR: User '${WEB_USER}' does not exist. Install Apache/PHP first." >&2
  exit 1
fi

if ! getent group "${WEB_GROUP}" >/dev/null 2>&1; then
  echo "ERROR: Group '${WEB_GROUP}' does not exist. Install Apache/PHP first." >&2
  exit 1
fi

if [[ ! -d "${DOC_ROOT}" ]]; then
  echo "Creating document root: ${DOC_ROOT}"
  "${SUDO[@]}" mkdir -p "${DOC_ROOT}"
fi

echo "Applying BluesGoal permissions"
echo "  DOC_ROOT=${DOC_ROOT}"
echo "  WEB_USER=${WEB_USER}"
echo "  WEB_GROUP=${WEB_GROUP}"
echo "  DATA_DIR=${DATA_DIR}"
echo "  RUN_DIR=${RUN_DIR}"
echo "  WORKER_LOG_DIR=${WORKER_LOG_DIR}"

# Local assets and web/app logs live under the document root but remain writable
# by Apache/PHP. Code and static app files are made root-owned below, then these
# writable directories are restored to the web user.
"${SUDO[@]}" mkdir -p \
  "${DOC_ROOT}/images" \
  "${DOC_ROOT}/mp3" \
  "${DOC_ROOT}/logs" \
  "${DATA_DIR}" \
  "${RUN_DIR}" \
  "${WORKER_LOG_DIR}"

# Application code/static files: Apache-readable, root/admin-writable.
"${SUDO[@]}" chown -R root:root "${DOC_ROOT}"
"${SUDO[@]}" find "${DOC_ROOT}" -type d -exec chmod 755 {} \;
"${SUDO[@]}" find "${DOC_ROOT}" -type f -exec chmod 644 {} \;
"${SUDO[@]}" find "${DOC_ROOT}" -name '*.py' -exec chmod 755 {} \;
"${SUDO[@]}" find "${DOC_ROOT}" -path '*/scripts/*.sh' -exec chmod 755 {} \;

# Runtime and local asset directories: writable where the web app needs it.
"${SUDO[@]}" chown -R "${WEB_USER}:${WEB_GROUP}" \
  "${DOC_ROOT}/images" \
  "${DOC_ROOT}/mp3" \
  "${DOC_ROOT}/logs"
"${SUDO[@]}" find "${DOC_ROOT}/images" "${DOC_ROOT}/mp3" "${DOC_ROOT}/logs" -type d -exec chmod 755 {} \;
"${SUDO[@]}" find "${DOC_ROOT}/images" "${DOC_ROOT}/mp3" "${DOC_ROOT}/logs" -type f -exec chmod 644 {} \;

"${SUDO[@]}" chown "${WEB_USER}:${WEB_GROUP}" "${DATA_DIR}" "${RUN_DIR}" "${WORKER_LOG_DIR}"
"${SUDO[@]}" chmod 775 "${DATA_DIR}" "${RUN_DIR}" "${WORKER_LOG_DIR}"

# Remove bytecode caches that may have been created before Python started using -B.
"${SUDO[@]}" find "${DOC_ROOT}" -type d -name __pycache__ -prune -exec rm -rf {} +

if [[ "${CREATE_TMPFILES}" == "1" ]]; then
  if command -v systemd-tmpfiles >/dev/null 2>&1; then
    echo "Creating /etc/tmpfiles.d/bluesgoal.conf for reboot-safe ${RUN_DIR}"
    printf 'd %s 0775 %s %s -\n' "${RUN_DIR}" "${WEB_USER}" "${WEB_GROUP}" \
      | "${SUDO[@]}" tee /etc/tmpfiles.d/bluesgoal.conf >/dev/null
    "${SUDO[@]}" systemd-tmpfiles --create /etc/tmpfiles.d/bluesgoal.conf
  else
    echo "systemd-tmpfiles not found; skipping tmpfiles.d setup"
  fi
else
  echo "Skipping tmpfiles.d setup because CREATE_TMPFILES=0 or --no-tmpfiles was used"
fi

cat <<SUMMARY

Permission setup complete.
Validate with:
  ls -ld ${DOC_ROOT} ${DOC_ROOT}/goalhorn ${DOC_ROOT}/config ${DOC_ROOT}/stylesheets
  ls -ld ${DOC_ROOT}/images ${DOC_ROOT}/mp3 ${DOC_ROOT}/logs ${DATA_DIR} ${RUN_DIR} ${WORKER_LOG_DIR}
  sudo -u ${WEB_USER} sudo -n python3 -B -c 'print("sudo ok")'
  curl -s http://localhost/goalhorn/_status.php
SUMMARY


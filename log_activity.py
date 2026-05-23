#!/usr/bin/python3

"""
Command-line bridge for logging activity from PHP endpoints.
"""

import sys
from logger import log_activity


def main():
    if len(sys.argv) < 2:
        print('Usage: log_activity.py <action> [message] [source]')
        return 1

    action = sys.argv[1]
    message = sys.argv[2] if len(sys.argv) > 2 else ''
    source = sys.argv[3] if len(sys.argv) > 3 else 'web_ui'
    log_activity(action, message, source)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

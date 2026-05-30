#!/usr/bin/python3
"""Backward-compatible wrapper for the shared goal horn action runner."""

import sys
from pathlib import Path

GOALHORN_DIR = Path(__file__).resolve().parents[1]
if str(GOALHORN_DIR) not in sys.path:
    sys.path.insert(0, str(GOALHORN_DIR))

from action_runner import main


if __name__ == "__main__":
    raise SystemExit(main(["bluesgoal_winterclassic"]))

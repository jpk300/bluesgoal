#!/usr/bin/python3
"""Automated NHL feed worker for the Blues goal light."""

import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

try:
    import fcntl
except ImportError:
    fcntl = None

TEAM_ABBREV = "STL"
SCHEDULE_URL = "https://api-web.nhle.com/v1/club-schedule-season/STL/now"
PLAY_BY_PLAY_URL = "https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"

SCHEDULE_CHECK_SECONDS = 6 * 60 * 60
PRE_GAME_WAKE_SECONDS = 10 * 60
PRE_GAME_POLL_SECONDS = 30
LIVE_POLL_SECONDS = 3
HTTP_TIMEOUT_SECONDS = 8

ENABLED_FILE = "/tmp/bluesgoal_nhl_feed_enabled"
STATUS_FILE = "/tmp/bluesgoal_nhl_feed_status.json"
STATE_FILE = "/tmp/bluesgoal_nhl_feed_state.json"
PROCESS_LOCK_FILE = "/tmp/bluesgoal_nhl_feed.lock"
ACTION_LOCK_FILE = "/tmp/bluesgoal_action.lock"

WINTER_CLASSIC_SCRIPT = "/var/www/html/goalhorn/bluesgoal_winterclassic/bluesgoal_winterclassic_master.py"
LOG_ACTIVITY_SCRIPT = "/var/www/html/log_activity.py"
LIVE_STATES = {"LIVE", "CRIT"}
FINISHED_STATES = {"FINAL", "OFF"}


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def iso_now():
    return utc_now().isoformat()


def parse_utc(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_enabled():
    try:
        with open(ENABLED_FILE, "r", encoding="utf-8") as handle:
            return handle.read().strip() == "1"
    except FileNotFoundError:
        return False


def wait_enabled(seconds):
    end_at = time.monotonic() + max(0, seconds)
    while read_enabled() and time.monotonic() < end_at:
        time.sleep(min(15, end_at - time.monotonic()))


def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path, payload):
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


def update_status(**updates):
    status = read_json(STATUS_FILE, {})
    status.update(updates)
    status["updated_at"] = iso_now()
    write_json(STATUS_FILE, status)


def log_activity(action, message):
    if os.path.exists(LOG_ACTIVITY_SCRIPT):
        subprocess.Popen(
            ["python3", LOG_ACTIVITY_SCRIPT, action, message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def fetch_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "bluesgoal-nhl-feed/1.0"})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def team_abbrev(team):
    abbrev = team.get("abbrev") if isinstance(team, dict) else ""
    if isinstance(abbrev, str):
        return abbrev
    if isinstance(abbrev, dict):
        return abbrev.get("default", "")
    return team.get("triCode", "") if isinstance(team, dict) else ""


def blues_team_id(game):
    for side in ("awayTeam", "homeTeam"):
        team = game.get(side, {})
        if team_abbrev(team) == TEAM_ABBREV:
            return team.get("id")
    return None


def score_line(game):
    away = game.get("awayTeam", {})
    home = game.get("homeTeam", {})
    return f"{team_abbrev(away)} {away.get('score', 0)}, {team_abbrev(home)} {home.get('score', 0)}"


def next_blues_game(schedule):
    now = utc_now()
    candidates = []
    for game in schedule.get("games", []):
        if blues_team_id(game) is None:
            continue
        state = game.get("gameState", "")
        if state in FINISHED_STATES:
            continue
        start_time = parse_utc(game["startTimeUTC"])
        if start_time >= now - dt.timedelta(hours=5) or state in LIVE_STATES:
            candidates.append((start_time, game))
    return min(candidates, key=lambda item: item[0])[1] if candidates else None


def acquire_lock(path, blocking):
    handle = open(path, "w", encoding="utf-8")
    if fcntl is None:
        return handle
    flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
    try:
        fcntl.flock(handle, flags)
        return handle
    except BlockingIOError:
        handle.close()
        return None


def release_lock(handle):
    if handle and fcntl is not None:
        fcntl.flock(handle, fcntl.LOCK_UN)
    if handle:
        handle.close()


def trigger_winter_classic(game_id, event_id):
    message = f"NHL API detected Blues goal: game {game_id}, event {event_id}"
    log_activity("nhl_api_goal", message)
    update_status(message="Blues goal detected; triggering Winter Classic", last_trigger=message, last_trigger_at=iso_now())

    action_lock = acquire_lock(ACTION_LOCK_FILE, blocking=True)
    try:
        result = subprocess.run(
            ["sudo", "python3", WINTER_CLASSIC_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=90,
            check=False,
        )
    finally:
        release_lock(action_lock)

    output = (result.stdout or result.stderr or "").strip()
    if result.returncode == 0:
        update_status(message="Winter Classic triggered by NHL API", last_trigger_output=output)
        log_activity("nhl_api_goal_complete", "Winter Classic goal horn triggered by NHL API")
    else:
        update_status(message="NHL API trigger failed", last_error=output or f"Exit code {result.returncode}")
        log_activity("nhl_api_goal_error", output or f"Exit code {result.returncode}")


def poll_game(game):
    game_id = str(game["id"])
    state = read_json(STATE_FILE, {})
    seen_goal_events = set(state.get("seen_goal_events", {}).get(game_id, []))
    baseline_ready = bool(state.get("baseline_ready", {}).get(game_id))

    while read_enabled():
        data = fetch_json(PLAY_BY_PLAY_URL.format(game_id=game_id))
        game_state = data.get("gameState", game.get("gameState", ""))
        current_game = {
            "id": game_id,
            "awayTeam": data.get("awayTeam", game.get("awayTeam", {})),
            "homeTeam": data.get("homeTeam", game.get("homeTeam", {})),
        }
        stl_id = blues_team_id(current_game)

        update_status(
            enabled=True,
            running=True,
            mode="live" if game_state in LIVE_STATES else "pregame",
            message="Watching live play-by-play" if game_state in LIVE_STATES else "Waiting for puck drop",
            watched_game_id=game_id,
            game_state=game_state,
            game=score_line(current_game),
            live_poll_seconds=LIVE_POLL_SECONDS,
            last_poll_at=iso_now(),
        )

        if game_state in FINISHED_STATES:
            state.setdefault("baseline_ready", {})[game_id] = False
            state.setdefault("seen_goal_events", {})[game_id] = sorted(seen_goal_events)
            write_json(STATE_FILE, state)
            return

        goal_events = []
        for play in data.get("plays", []):
            details = play.get("details", {})
            event_id = str(play.get("eventId"))
            if play.get("typeDescKey") == "goal" and details.get("eventOwnerTeamId") == stl_id:
                goal_events.append(event_id)

        if not baseline_ready:
            seen_goal_events.update(goal_events)
            baseline_ready = True
            update_status(message="Goal baseline set; watching for new Blues goals")
        elif game_state in LIVE_STATES:
            for event_id in goal_events:
                if event_id not in seen_goal_events:
                    seen_goal_events.add(event_id)
                    trigger_winter_classic(game_id, event_id)

        state.setdefault("seen_goal_events", {})[game_id] = sorted(seen_goal_events)
        state.setdefault("baseline_ready", {})[game_id] = baseline_ready
        write_json(STATE_FILE, state)
        wait_enabled(LIVE_POLL_SECONDS if game_state in LIVE_STATES else PRE_GAME_POLL_SECONDS)


def main():
    process_lock = acquire_lock(PROCESS_LOCK_FILE, blocking=False)
    if process_lock is None:
        update_status(enabled=read_enabled(), running=True, message="NHL feed worker already running")
        return 0

    try:
        update_status(enabled=read_enabled(), running=True, mode="schedule", message="NHL feed worker started")
        while read_enabled():
            try:
                schedule = fetch_json(SCHEDULE_URL)
                game = next_blues_game(schedule)
                if not game:
                    update_status(
                        enabled=True,
                        running=True,
                        mode="schedule",
                        message="No upcoming Blues game found; checking schedule every 6 hours",
                        schedule_poll_seconds=SCHEDULE_CHECK_SECONDS,
                        last_schedule_check_at=iso_now(),
                    )
                    wait_enabled(SCHEDULE_CHECK_SECONDS)
                    continue

                start_time = parse_utc(game["startTimeUTC"])
                seconds_until_wake = (start_time - utc_now()).total_seconds() - PRE_GAME_WAKE_SECONDS
                if seconds_until_wake > 0:
                    update_status(
                        enabled=True,
                        running=True,
                        mode="schedule",
                        message="Blues game scheduled; sleeping until pregame watch",
                        watched_game_id=str(game["id"]),
                        next_game_start_utc=game["startTimeUTC"],
                        schedule_poll_seconds=SCHEDULE_CHECK_SECONDS,
                        last_schedule_check_at=iso_now(),
                    )
                    wait_enabled(min(SCHEDULE_CHECK_SECONDS, seconds_until_wake))
                    continue

                poll_game(game)
            except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError, json.JSONDecodeError) as error:
                update_status(enabled=True, running=True, message="NHL API unavailable", last_error=str(error))
                log_activity("nhl_api_error", str(error))
                wait_enabled(PRE_GAME_POLL_SECONDS)

        update_status(enabled=False, running=False, mode="manual", message="Manual buttons only")
        return 0
    finally:
        release_lock(process_lock)


if __name__ == "__main__":
    sys.exit(main())
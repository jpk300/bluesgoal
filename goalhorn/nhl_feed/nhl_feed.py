#!/usr/bin/python3
"""Automated NHL feed worker for the goal light."""

import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

try:
    import fcntl
except ImportError:
    fcntl = None

DEFAULT_TEAM_ABBREV = "STL"
SCHEDULE_URL = "https://api-web.nhle.com/v1/club-schedule-season/{team}/now"
PLAY_BY_PLAY_URL = "https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"

SCHEDULE_CHECK_SECONDS = 6 * 60 * 60
PRE_GAME_WAKE_SECONDS = 10 * 60
PRE_GAME_POLL_SECONDS = 30
LIVE_POLL_SECONDS = 3
HTTP_TIMEOUT_SECONDS = 8

ENABLED_FILE = "/tmp/bluesgoal_nhl_feed_enabled"
SETTINGS_FILE = "/tmp/bluesgoal_nhl_feed_settings.json"
STATUS_FILE = "/tmp/bluesgoal_nhl_feed_status.json"
STATE_FILE = "/tmp/bluesgoal_nhl_feed_state.json"
PROCESS_LOCK_FILE = "/tmp/bluesgoal_nhl_feed.lock"
ACTION_LOCK_FILE = "/tmp/bluesgoal_action.lock"

GOALHORN_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GOALHORN_DIR.parent
WINTER_CLASSIC_SCRIPT = str(GOALHORN_DIR / "bluesgoal_winterclassic" / "bluesgoal_winterclassic_master.py")
LOG_ACTIVITY_SCRIPT = str(REPO_ROOT / "log_activity.py")
LIVE_STATES = {"LIVE", "CRIT"}
FINISHED_STATES = {"FINAL", "OFF"}
VALID_TEAMS = {
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL", "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WPG", "WSH"
}


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


def read_settings():
    settings = read_json(SETTINGS_FILE, {})
    team = str(settings.get("source_team", DEFAULT_TEAM_ABBREV)).upper()
    if team not in VALID_TEAMS:
        team = DEFAULT_TEAM_ABBREV
    return {"source_team": team}


def wait_enabled(seconds, source_team=None):
    end_at = time.monotonic() + max(0, seconds)
    while read_enabled() and time.monotonic() < end_at:
        if source_team and read_settings()["source_team"] != source_team:
            return
        time.sleep(min(15, end_at - time.monotonic()))


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


def monitored_team_id(game, source_team):
    for side in ("awayTeam", "homeTeam"):
        team = game.get(side, {})
        if team_abbrev(team) == source_team:
            return team.get("id")
    return None


def score_line(game):
    away = game.get("awayTeam", {})
    home = game.get("homeTeam", {})
    return f"{team_abbrev(away)} {away.get('score', 0)}, {team_abbrev(home)} {home.get('score', 0)}"


def has_game_today(schedule, source_team):
    today = utc_now().date()
    for game in schedule.get("games", []):
        if monitored_team_id(game, source_team) is None:
            continue
        start_time = parse_utc(game["startTimeUTC"])
        if start_time.date() == today and game.get("gameState", "") not in FINISHED_STATES:
            return True
    return False


def next_team_game(schedule, source_team):
    now = utc_now()
    candidates = []
    for game in schedule.get("games", []):
        if monitored_team_id(game, source_team) is None:
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


def trigger_winter_classic(source_team, game_id, event_id):
    message = f"NHL API detected {source_team} goal: game {game_id}, event {event_id}"
    log_activity("nhl_api_goal", message)
    update_status(message="Goal detected; triggering Winter Classic", last_trigger=message, last_trigger_at=iso_now())

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


def poll_game(game, source_team):
    game_id = str(game["id"])
    state = read_json(STATE_FILE, {})
    seen_goal_events = set(state.get("seen_goal_events", {}).get(game_id, []))
    baseline_ready = bool(state.get("baseline_ready", {}).get(game_id))

    while read_enabled() and read_settings()["source_team"] == source_team:
        data = fetch_json(PLAY_BY_PLAY_URL.format(game_id=game_id))
        game_state = data.get("gameState", game.get("gameState", ""))
        current_game = {
            "id": game_id,
            "awayTeam": data.get("awayTeam", game.get("awayTeam", {})),
            "homeTeam": data.get("homeTeam", game.get("homeTeam", {})),
        }
        source_team_id = monitored_team_id(current_game, source_team)
        current_poll_seconds = LIVE_POLL_SECONDS if game_state in LIVE_STATES else PRE_GAME_POLL_SECONDS

        update_status(
            enabled=True,
            running=True,
            source_team=source_team,
            mode="live" if game_state in LIVE_STATES else "pregame",
            message="Watching live play-by-play" if game_state in LIVE_STATES else "Waiting for puck drop",
            watched_game_id=game_id,
            game_state=game_state,
            game=score_line(current_game),
            current_poll_seconds=current_poll_seconds,
            live_poll_seconds=LIVE_POLL_SECONDS,
            pregame_poll_seconds=PRE_GAME_POLL_SECONDS,
            schedule_poll_seconds=SCHEDULE_CHECK_SECONDS,
            game_today=True,
            triggers_expected=game_state not in FINISHED_STATES,
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
            if play.get("typeDescKey") == "goal" and details.get("eventOwnerTeamId") == source_team_id:
                goal_events.append(event_id)

        if not baseline_ready:
            seen_goal_events.update(goal_events)
            baseline_ready = True
            update_status(message="Goal baseline set; watching for new goals")
        elif game_state in LIVE_STATES:
            for event_id in goal_events:
                if event_id not in seen_goal_events:
                    seen_goal_events.add(event_id)
                    trigger_winter_classic(source_team, game_id, event_id)

        state.setdefault("seen_goal_events", {})[game_id] = sorted(seen_goal_events)
        state.setdefault("baseline_ready", {})[game_id] = baseline_ready
        write_json(STATE_FILE, state)
        wait_enabled(current_poll_seconds, source_team)


def main():
    process_lock = acquire_lock(PROCESS_LOCK_FILE, blocking=False)
    if process_lock is None:
        update_status(enabled=read_enabled(), running=True, message="NHL feed worker already running")
        return 0

    try:
        update_status(enabled=read_enabled(), running=True, mode="schedule", message="NHL feed worker started")
        while read_enabled():
            settings = read_settings()
            source_team = settings["source_team"]
            try:
                schedule = fetch_json(SCHEDULE_URL.format(team=source_team))
                game = next_team_game(schedule, source_team)
                game_today = has_game_today(schedule, source_team)
                if not game:
                    update_status(
                        enabled=True,
                        running=True,
                        source_team=source_team,
                        mode="schedule",
                        message=f"No upcoming {source_team} game found; checking schedule every 6 hours",
                        schedule_poll_seconds=SCHEDULE_CHECK_SECONDS,
                        current_poll_seconds=SCHEDULE_CHECK_SECONDS,
                        game_today=game_today,
                        triggers_expected=False,
                        watched_game_id=None,
                        last_schedule_check_at=iso_now(),
                    )
                    wait_enabled(SCHEDULE_CHECK_SECONDS, source_team)
                    continue

                start_time = parse_utc(game["startTimeUTC"])
                seconds_until_wake = (start_time - utc_now()).total_seconds() - PRE_GAME_WAKE_SECONDS
                if seconds_until_wake > 0:
                    update_status(
                        enabled=True,
                        running=True,
                        source_team=source_team,
                        mode="schedule",
                        message=f"{source_team} game scheduled; sleeping until pregame watch",
                        watched_game_id=str(game["id"]),
                        next_game_start_utc=game["startTimeUTC"],
                        schedule_poll_seconds=SCHEDULE_CHECK_SECONDS,
                        current_poll_seconds=min(SCHEDULE_CHECK_SECONDS, int(seconds_until_wake)),
                        game_today=game_today,
                        triggers_expected=game_today,
                        last_schedule_check_at=iso_now(),
                    )
                    wait_enabled(min(SCHEDULE_CHECK_SECONDS, seconds_until_wake), source_team)
                    continue

                poll_game(game, source_team)
            except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError, json.JSONDecodeError) as error:
                update_status(enabled=True, running=True, source_team=source_team, message="NHL API unavailable", last_error=str(error))
                log_activity("nhl_api_error", str(error))
                wait_enabled(PRE_GAME_POLL_SECONDS, source_team)

        update_status(enabled=False, running=False, mode="manual", message="Manual buttons only", triggers_expected=False)
        return 0
    finally:
        release_lock(process_lock)


if __name__ == "__main__":
    sys.exit(main())
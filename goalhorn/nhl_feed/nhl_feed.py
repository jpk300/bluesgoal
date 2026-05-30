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

DATA_DIR = Path("/var/lib/bluesgoal")
RUN_DIR = Path("/run/bluesgoal")
LOG_DIR = Path("/var/log/bluesgoal")
ENABLED_FILE = DATA_DIR / "nhl_feed_enabled"
SETTINGS_FILE = DATA_DIR / "nhl_feed_settings.json"
STATUS_FILE = RUN_DIR / "nhl_feed_status.json"
STATE_FILE = DATA_DIR / "nhl_feed_state.json"
ACTION_LOCK_FILE = RUN_DIR / "action.lock"
PROCESS_LOCK_FILE = RUN_DIR / "nhl_feed.lock"

LEGACY_ENABLED_FILE = Path("/tmp/bluesgoal_nhl_feed_enabled")
LEGACY_SETTINGS_FILE = Path("/tmp/bluesgoal_nhl_feed_settings.json")
LEGACY_STATUS_FILE = Path("/tmp/bluesgoal_nhl_feed_status.json")
LEGACY_STATE_FILE = Path("/tmp/bluesgoal_nhl_feed_state.json")
NHL_FEED_DIR = Path(__file__).resolve().parent
GOALHORN_DIR = NHL_FEED_DIR.parent
REPO_ROOT = GOALHORN_DIR.parent
NHL_TEAMS_FILE = REPO_ROOT / "config" / "nhl_teams.json"
ACTION_RUNNER_SCRIPT = str(GOALHORN_DIR / "action_runner.py")
LOG_ACTIVITY_SCRIPT = str(REPO_ROOT / "log_activity.py")
LIVE_STATES = {"LIVE", "CRIT"}
FINISHED_STATES = {"FINAL", "OFF"}


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def iso_now():
    return utc_now().isoformat()


def parse_utc(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_enabled():
    migrate_legacy_files()
    try:
        with open(ENABLED_FILE, "r", encoding="utf-8") as handle:
            return handle.read().strip() == "1"
    except FileNotFoundError:
        return False


def ensure_runtime_dirs():
    for directory in (DATA_DIR, RUN_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def migrate_legacy_file(new_path, legacy_path):
    if new_path.exists() or legacy_path is None or not legacy_path.exists():
        return
    new_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        new_path.write_bytes(legacy_path.read_bytes())
    except OSError:
        return


def migrate_legacy_files():
    migrate_legacy_file(ENABLED_FILE, LEGACY_ENABLED_FILE)
    migrate_legacy_file(SETTINGS_FILE, LEGACY_SETTINGS_FILE)
    migrate_legacy_file(STATUS_FILE, LEGACY_STATUS_FILE)
    migrate_legacy_file(STATE_FILE, LEGACY_STATE_FILE)


def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


def read_team_map():
    payload = read_json(NHL_TEAMS_FILE, {})
    teams = payload.get("teams", {}) if isinstance(payload, dict) else {}
    normalized = {
        str(abbrev).strip().upper(): str(name)
        for abbrev, name in teams.items()
        if str(abbrev).strip()
    }
    return normalized or {DEFAULT_TEAM_ABBREV: "St. Louis Blues"}


def valid_teams():
    return set(read_team_map().keys())


def read_settings():
    migrate_legacy_files()
    settings = read_json(SETTINGS_FILE, {})
    team = str(settings.get("source_team", DEFAULT_TEAM_ABBREV)).upper()
    if team not in valid_teams():
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


def is_worker_pid(pid):
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, OSError):
        return False
    return "python3" in cmdline and str(Path(__file__).resolve()) in cmdline


def cleanup_stale_lock(path):
    lock_path = Path(path)
    if not lock_path.exists():
        return

    try:
        content = lock_path.read_text(encoding="utf-8").strip()
    except PermissionError:
        lock_path.unlink()
        return
    except OSError:
        content = ""

    try:
        pid = int(content) if content else None
    except ValueError:
        pid = None

    if pid and is_worker_pid(pid):
        return

    if not pid and fcntl is not None:
        try:
            with open(lock_path, "a+", encoding="utf-8") as handle:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(handle, fcntl.LOCK_UN)
        except BlockingIOError:
            return
        except PermissionError:
            pass

    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass


def acquire_lock(path, blocking):
    lock_path = Path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    cleanup_stale_lock(lock_path)
    handle = open(lock_path, "a+", encoding="utf-8")
    try:
        os.chmod(lock_path, 0o666)
    except PermissionError:
        pass
    if fcntl is not None:
        flags = fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB)
        try:
            fcntl.flock(handle, flags)
        except BlockingIOError:
            handle.close()
            return None
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    os.fsync(handle.fileno())
    return handle


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
            ["sudo", "-n", "python3", ACTION_RUNNER_SCRIPT, "bluesgoal_winterclassic"],
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
            next_game_start_utc=game.get("startTimeUTC"),
            live_poll_seconds=LIVE_POLL_SECONDS,
            pregame_poll_seconds=PRE_GAME_POLL_SECONDS,
            schedule_poll_seconds=SCHEDULE_CHECK_SECONDS,
            game_today=True,
            triggers_expected=game_state not in FINISHED_STATES,
            last_poll_at=iso_now(),
            last_error=None,
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
    ensure_runtime_dirs()
    migrate_legacy_files()
    try:
        process_lock = acquire_lock(PROCESS_LOCK_FILE, blocking=False)
    except OSError as error:
        update_status(
            enabled=read_enabled(),
            running=False,
            message="NHL feed worker cannot create process lock",
            last_error=f"Unable to create worker lock {PROCESS_LOCK_FILE}: {error}",
        )
        log_activity("nhl_api_lock_error", str(error))
        return 1
    if process_lock is None:
        update_status(enabled=read_enabled(), running=True, message="NHL feed worker already running")
        return 0

    try:
        while read_enabled():
            settings = read_settings()
            source_team = settings["source_team"]
            update_status(
                enabled=True,
                running=True,
                source_team=source_team,
                mode="schedule",
                message="Checking NHL schedule",
                current_poll_seconds=PRE_GAME_POLL_SECONDS,
                schedule_poll_seconds=SCHEDULE_CHECK_SECONDS,
                game_today=None,
                triggers_expected=None,
                last_error=None,
            )
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
                        next_game_start_utc=None,
                        last_schedule_check_at=iso_now(),
                        last_error=None,
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
                        last_error=None,
                    )
                    wait_enabled(min(SCHEDULE_CHECK_SECONDS, seconds_until_wake), source_team)
                    continue

                poll_game(game, source_team)
            except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError, json.JSONDecodeError) as error:
                update_status(
                    enabled=True,
                    running=True,
                    source_team=source_team,
                    mode="schedule",
                    message="NHL API unavailable",
                    current_poll_seconds=PRE_GAME_POLL_SECONDS,
                    last_error=str(error),
                )
                log_activity("nhl_api_error", str(error))
                wait_enabled(PRE_GAME_POLL_SECONDS, source_team)

        update_status(enabled=False, running=False, mode="manual", message="Manual buttons only", triggers_expected=False)
        return 0
    finally:
        release_lock(process_lock)


if __name__ == "__main__":
    sys.exit(main())

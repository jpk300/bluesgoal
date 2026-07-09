#!/usr/bin/python3
"""Automated MLB run trigger worker for the goal light."""

import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

try:
    import fcntl
except ImportError:
    fcntl = None

DEFAULT_TEAM_ID = "138"
SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"

SCHEDULE_CHECK_SECONDS = 6 * 60 * 60
PRE_GAME_WAKE_SECONDS = 10 * 60
PRE_GAME_POLL_SECONDS = 30
LIVE_POLL_SECONDS = 8
HTTP_TIMEOUT_SECONDS = 8
LOCAL_TIMEZONE = ZoneInfo(os.environ.get("BLUESGOAL_TIMEZONE", "America/Chicago"))

DATA_DIR = Path(os.environ.get("BLUESGOAL_DATA_DIR", "/var/lib/bluesgoal"))
RUN_DIR = Path(os.environ.get("BLUESGOAL_RUN_DIR", "/run/bluesgoal"))
LOG_DIR = Path(os.environ.get("BLUESGOAL_WORKER_LOG_DIR", "/var/log/bluesgoal"))
ENABLED_FILE = DATA_DIR / "mlb_feed_enabled"
SETTINGS_FILE = DATA_DIR / "mlb_feed_settings.json"
STATUS_FILE = RUN_DIR / "mlb_feed_status.json"
STATE_FILE = DATA_DIR / "mlb_feed_state.json"
ACTION_LOCK_FILE = RUN_DIR / "action.lock"
PROCESS_LOCK_FILE = RUN_DIR / "mlb_feed.lock"

MLB_FEED_DIR = Path(__file__).resolve().parent
GOALHORN_DIR = MLB_FEED_DIR.parent
REPO_ROOT = GOALHORN_DIR.parent
MLB_TEAMS_FILE = REPO_ROOT / "config" / "mlb_teams.json"
ACTION_RUNNER_SCRIPT = str(GOALHORN_DIR / "action_runner.py")
LOG_ACTIVITY_SCRIPT = str(REPO_ROOT / "log_activity.py")
LIGHTS_ACTION = "mlb_run_lights"
LIVE_STATES = {"Live"}
FINISHED_STATES = {"Final"}


def utc_now():
    return dt.datetime.now(dt.timezone.utc)


def local_today():
    return utc_now().astimezone(LOCAL_TIMEZONE).date()


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


def ensure_runtime_dirs():
    for directory in (DATA_DIR, RUN_DIR, LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)


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
    payload = read_json(MLB_TEAMS_FILE, {})
    teams = payload.get("teams", {}) if isinstance(payload, dict) else {}
    normalized = {
        str(team_id).strip(): str(name)
        for team_id, name in teams.items()
        if str(team_id).strip().isdigit()
    }
    return normalized or {DEFAULT_TEAM_ID: "St. Louis Cardinals"}


def valid_teams():
    return set(read_team_map().keys())


def team_label(team_id):
    return read_team_map().get(str(team_id), str(team_id))


def read_settings():
    settings = read_json(SETTINGS_FILE, {})
    team = str(settings.get("source_team", DEFAULT_TEAM_ID))
    if team not in valid_teams():
        team = DEFAULT_TEAM_ID
    return {"source_team": team}


def wait_enabled(seconds, source_team=None):
    end_at = time.monotonic() + max(0, seconds)
    while read_enabled() and time.monotonic() < end_at:
        if source_team and read_settings()["source_team"] != source_team:
            return
        time.sleep(min(1, end_at - time.monotonic()))


def update_status(**updates):
    status = read_json(STATUS_FILE, {})
    status.update(updates)
    status["updated_at"] = iso_now()
    write_json(STATUS_FILE, status)


def log_activity(action, message):
    if os.path.exists(LOG_ACTIVITY_SCRIPT):
        subprocess.Popen(
            ["python3", "-B", LOG_ACTIVITY_SCRIPT, action, message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def fetch_json(url, params):
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": "bluesgoal-mlb-feed/1.0"})
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_schedule(team_id, start_date, end_date):
    return fetch_json(SCHEDULE_URL, {
        "sportId": "1",
        "teamId": team_id,
        "hydrate": "linescore",
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
    })


def fetch_game(game_pk):
    return fetch_json(SCHEDULE_URL, {
        "sportId": "1",
        "gamePk": str(game_pk),
        "hydrate": "linescore",
    })


def games_from_schedule(schedule):
    games = []
    for date_entry in schedule.get("dates", []):
        games.extend(date_entry.get("games", []))
    return games


def game_state(game):
    status = game.get("status", {})
    return status.get("abstractGameState") or status.get("detailedState") or "Unknown"


def team_side(game, team_id):
    for side in ("away", "home"):
        team = game.get("teams", {}).get(side, {}).get("team", {})
        if str(team.get("id")) == str(team_id):
            return side
    return None


def team_abbrev(game, side):
    team = game.get("teams", {}).get(side, {}).get("team", {})
    return team.get("abbreviation") or team.get("teamName") or str(team.get("id", ""))


def side_runs(game, side):
    linescore = game.get("linescore", {}).get("teams", {}).get(side, {})
    if "runs" in linescore:
        return int(linescore.get("runs") or 0)
    return int(game.get("teams", {}).get(side, {}).get("score") or 0)


def monitored_team_runs(game, team_id):
    side = team_side(game, team_id)
    if side is None:
        return 0
    return side_runs(game, side)


def score_line(game):
    away = team_abbrev(game, "away")
    home = team_abbrev(game, "home")
    return f"{away} {side_runs(game, 'away')}, {home} {side_runs(game, 'home')}"


def has_game_today(schedule, team_id):
    today = local_today()
    for game in games_from_schedule(schedule):
        if team_side(game, team_id) is None:
            continue
        game_time = parse_utc(game["gameDate"]).astimezone(LOCAL_TIMEZONE)
        if game_time.date() == today and game_state(game) not in FINISHED_STATES:
            return True
    return False


def next_team_game(schedule, team_id):
    now = utc_now()
    candidates = []
    for game in games_from_schedule(schedule):
        if team_side(game, team_id) is None:
            continue
        state = game_state(game)
        if state in FINISHED_STATES:
            continue
        start_time = parse_utc(game["gameDate"])
        if start_time >= now - dt.timedelta(hours=6) or state in LIVE_STATES:
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


def trigger_run_lights(source_team, game_pk, runs_added, total_runs):
    label = team_label(source_team)
    message = f"MLB API detected {label} run: game {game_pk}, +{runs_added}, total {total_runs}"
    log_activity("mlb_api_run", message)
    update_status(message="Run detected; triggering lights", last_trigger=message, last_trigger_at=iso_now())

    action_lock = acquire_lock(ACTION_LOCK_FILE, blocking=True)
    try:
        result = subprocess.run(
            ["sudo", "-n", "python3", "-B", ACTION_RUNNER_SCRIPT, LIGHTS_ACTION],
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
        update_status(message="MLB run lights triggered", last_trigger_output=output)
        log_activity("mlb_api_run_complete", "MLB run lights triggered by API")
    else:
        update_status(message="MLB API trigger failed", last_error=output or f"Exit code {result.returncode}")
        log_activity("mlb_api_run_error", output or f"Exit code {result.returncode}")


def poll_game(game, source_team):
    game_pk = str(game["gamePk"])
    state = read_json(STATE_FILE, {})
    game_state_record = state.setdefault("games", {}).setdefault(game_pk, {})
    baseline_ready = bool(game_state_record.get("baseline_ready"))
    last_runs = int(game_state_record.get("last_runs", 0))

    while read_enabled() and read_settings()["source_team"] == source_team:
        data = fetch_game(game_pk)
        games = games_from_schedule(data)
        current_game = games[0] if games else game
        current_state = game_state(current_game)
        current_runs = monitored_team_runs(current_game, source_team)
        current_poll_seconds = LIVE_POLL_SECONDS if current_state in LIVE_STATES else PRE_GAME_POLL_SECONDS

        update_status(
            enabled=True,
            running=True,
            source_team=source_team,
            source_team_label=team_label(source_team),
            mode="live" if current_state in LIVE_STATES else "pregame",
            message="Watching live MLB linescore" if current_state in LIVE_STATES else "Waiting for first pitch",
            watched_game_id=game_pk,
            game_state=current_state,
            game=score_line(current_game),
            source_team_runs=current_runs,
            current_poll_seconds=current_poll_seconds,
            next_game_start_utc=current_game.get("gameDate", game.get("gameDate")),
            live_poll_seconds=LIVE_POLL_SECONDS,
            pregame_poll_seconds=PRE_GAME_POLL_SECONDS,
            schedule_poll_seconds=SCHEDULE_CHECK_SECONDS,
            game_today=True,
            triggers_expected=current_state not in FINISHED_STATES,
            last_poll_at=iso_now(),
            last_error=None,
        )

        if current_state in FINISHED_STATES:
            game_state_record["baseline_ready"] = False
            game_state_record["last_runs"] = current_runs
            write_json(STATE_FILE, state)
            return

        if not baseline_ready:
            baseline_ready = True
            last_runs = current_runs
            update_status(message="Run baseline set; watching for new runs")
        elif current_state in LIVE_STATES and current_runs > last_runs:
            runs_added = current_runs - last_runs
            trigger_run_lights(source_team, game_pk, runs_added, current_runs)
            last_runs = current_runs
        else:
            last_runs = max(last_runs, current_runs)

        game_state_record["baseline_ready"] = baseline_ready
        game_state_record["last_runs"] = last_runs
        write_json(STATE_FILE, state)
        wait_enabled(current_poll_seconds, source_team)


def main():
    ensure_runtime_dirs()
    try:
        process_lock = acquire_lock(PROCESS_LOCK_FILE, blocking=False)
    except OSError as error:
        update_status(
            enabled=read_enabled(),
            running=False,
            message="MLB feed worker cannot create process lock",
            last_error=f"Unable to create worker lock {PROCESS_LOCK_FILE}: {error}",
        )
        log_activity("mlb_api_lock_error", str(error))
        return 1
    if process_lock is None:
        update_status(enabled=read_enabled(), running=True, message="MLB feed worker already running")
        return 0

    try:
        while read_enabled():
            settings = read_settings()
            source_team = settings["source_team"]
            today = local_today()
            update_status(
                enabled=True,
                running=True,
                source_team=source_team,
                source_team_label=team_label(source_team),
                mode="schedule",
                message="Checking MLB schedule",
                current_poll_seconds=PRE_GAME_POLL_SECONDS,
                schedule_poll_seconds=SCHEDULE_CHECK_SECONDS,
                game_today=None,
                triggers_expected=None,
                last_error=None,
            )
            try:
                schedule = fetch_schedule(source_team, today - dt.timedelta(days=1), today + dt.timedelta(days=7))
                game = next_team_game(schedule, source_team)
                game_today = has_game_today(schedule, source_team)
                if not game:
                    update_status(
                        enabled=True,
                        running=True,
                        source_team=source_team,
                        source_team_label=team_label(source_team),
                        mode="schedule",
                        message=f"No upcoming {team_label(source_team)} game found; checking schedule every 6 hours",
                        schedule_poll_seconds=SCHEDULE_CHECK_SECONDS,
                        current_poll_seconds=SCHEDULE_CHECK_SECONDS,
                        game_today=game_today,
                        triggers_expected=False,
                        watched_game_id=None,
                        game=None,
                        next_game_start_utc=None,
                        last_schedule_check_at=iso_now(),
                        last_error=None,
                    )
                    wait_enabled(SCHEDULE_CHECK_SECONDS, source_team)
                    continue

                start_time = parse_utc(game["gameDate"])
                seconds_until_wake = (start_time - utc_now()).total_seconds() - PRE_GAME_WAKE_SECONDS
                if seconds_until_wake > 0:
                    update_status(
                        enabled=True,
                        running=True,
                        source_team=source_team,
                        source_team_label=team_label(source_team),
                        mode="schedule",
                        message=f"{team_label(source_team)} game scheduled; sleeping until pregame watch",
                        watched_game_id=str(game["gamePk"]),
                        game=score_line(game),
                        next_game_start_utc=game["gameDate"],
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
                    source_team_label=team_label(source_team),
                    mode="schedule",
                    message="MLB API unavailable",
                    current_poll_seconds=PRE_GAME_POLL_SECONDS,
                    last_error=str(error),
                )
                log_activity("mlb_api_error", str(error))
                wait_enabled(PRE_GAME_POLL_SECONDS, source_team)

        update_status(enabled=False, running=False, mode="manual", message="MLB run trigger off", triggers_expected=False)
        return 0
    finally:
        release_lock(process_lock)


if __name__ == "__main__":
    sys.exit(main())

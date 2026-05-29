<?php
require_once __DIR__ . '/_helpers.php';

const NHL_FEED_ENABLED_FILE = '/tmp/bluesgoal_nhl_feed_enabled';
const NHL_FEED_SETTINGS_FILE = '/tmp/bluesgoal_nhl_feed_settings.json';
const NHL_FEED_STATUS_FILE = '/tmp/bluesgoal_nhl_feed_status.json';
const NHL_FEED_STATE_FILE = '/tmp/bluesgoal_nhl_feed_state.json';
const NHL_FEED_LOG = '/tmp/bluesgoal_nhl_feed.log';

function nhl_feed_valid_teams() {
    return ['ANA','BOS','BUF','CAR','CBJ','CGY','CHI','COL','DAL','DET','EDM','FLA','LAK','MIN','MTL','NJD','NSH','NYI','NYR','OTT','PHI','PIT','SEA','SJS','STL','TBL','TOR','UTA','VAN','VGK','WPG','WSH'];
}

function nhl_feed_settings() {
    $settings = [];
    if (file_exists(NHL_FEED_SETTINGS_FILE)) {
        $decoded = json_decode((string) @file_get_contents(NHL_FEED_SETTINGS_FILE), true);
        if (is_array($decoded)) {
            $settings = $decoded;
        }
    }

    $team = strtoupper((string) ($settings['source_team'] ?? 'STL'));
    if (!in_array($team, nhl_feed_valid_teams(), true)) {
        $team = 'STL';
    }

    return ['source_team' => $team];
}

function nhl_feed_write_settings($settings) {
    @file_put_contents(NHL_FEED_SETTINGS_FILE, json_encode($settings), LOCK_EX);
}

function nhl_feed_is_enabled() {
    return file_exists(NHL_FEED_ENABLED_FILE) && trim((string) @file_get_contents(NHL_FEED_ENABLED_FILE)) === '1';
}

function nhl_feed_read_status() {
    if (!file_exists(NHL_FEED_STATUS_FILE)) {
        return [];
    }

    $decoded = json_decode((string) @file_get_contents(NHL_FEED_STATUS_FILE), true);
    return is_array($decoded) ? $decoded : [];
}

function nhl_feed_script_path() {
    return __DIR__ . '/nhl_feed/nhl_feed.py';
}

function nhl_feed_is_running() {
    $script = nhl_feed_script_path();
    $output = [];
    $exitCode = 1;
    exec('pgrep -af ' . escapeshellarg($script), $output, $exitCode);

    if ($exitCode !== 0 || count($output) === 0) {
        return false;
    }

    foreach ($output as $line) {
        if (strpos($line, 'python3') !== false && strpos($line, $script) !== false) {
            return true;
        }
    }

    return false;
}

function nhl_feed_write_enabled($enabled) {
    @file_put_contents(NHL_FEED_ENABLED_FILE, $enabled ? '1' : '0', LOCK_EX);
}

function nhl_feed_write_status($updates) {
    $status = nhl_feed_read_status();
    $status = array_merge($status, $updates, [
        'updated_at' => gmdate('c')
    ]);
    @file_put_contents(NHL_FEED_STATUS_FILE, json_encode($status, JSON_PRETTY_PRINT), LOCK_EX);
}

function nhl_feed_recent_start_attempt($seconds = 30) {
    $status = nhl_feed_read_status();
    if (empty($status['last_worker_start_attempt_at'])) {
        return false;
    }

    $attemptAt = strtotime((string) $status['last_worker_start_attempt_at']);
    return $attemptAt !== false && (time() - $attemptAt) < $seconds;
}

function nhl_feed_worker_sudo_error() {
    $output = [];
    $exitCode = 0;
    exec('sudo -n python3 -c ' . escapeshellarg('import sys') . ' 2>&1', $output, $exitCode);
    return $exitCode === 0 ? null : trim(implode("\n", $output));
}

function nhl_feed_start_worker() {
    if (nhl_feed_is_running()) {
        return true;
    }

    if (nhl_feed_recent_start_attempt()) {
        return false;
    }

    $script = nhl_feed_script_path();
    if (!file_exists($script)) {
        nhl_feed_write_status([
            'enabled' => nhl_feed_is_enabled(),
            'running' => false,
            'message' => 'NHL feed worker script not found',
            'last_error' => 'Missing worker script: ' . $script,
            'current_poll_seconds' => null,
            'last_worker_start_attempt_at' => gmdate('c')
        ]);
        return false;
    }

    $sudoError = nhl_feed_worker_sudo_error();
    if ($sudoError !== null) {
        nhl_feed_write_status([
            'enabled' => true,
            'running' => false,
            'message' => 'NHL feed worker cannot start',
            'last_error' => $sudoError,
            'current_poll_seconds' => null,
            'last_worker_start_attempt_at' => gmdate('c')
        ]);
        return false;
    }

    nhl_feed_write_status([
        'enabled' => true,
        'running' => false,
        'message' => 'Starting NHL feed worker',
        'last_error' => null,
        'current_poll_seconds' => null,
        'last_worker_start_attempt_at' => gmdate('c')
    ]);

    $command = 'nohup sudo -n python3 ' . escapeshellarg($script)
        . ' >> ' . escapeshellarg(NHL_FEED_LOG)
        . ' 2>&1 &';
    @shell_exec($command);
    sleep(1);

    if (nhl_feed_is_running()) {
        nhl_feed_write_status([
            'enabled' => true,
            'running' => true,
            'message' => 'NHL feed worker started',
            'last_error' => null
        ]);
        return true;
    }

    nhl_feed_write_status([
        'enabled' => true,
        'running' => false,
        'message' => 'NHL feed worker failed to start',
        'last_error' => 'Worker process was not found after launch; check ' . NHL_FEED_LOG
    ]);
    return false;
}

function nhl_feed_payload($message = null) {
    $enabled = nhl_feed_is_enabled();
    return [
        'success' => true,
        'enabled' => $enabled,
        'running' => nhl_feed_is_running(),
        'settings' => nhl_feed_settings(),
        'teams' => nhl_feed_valid_teams(),
        'message' => $message ?: ($enabled ? 'NHL API feed enabled' : 'Manual buttons only'),
        'data' => nhl_feed_read_status(),
        'timestamp' => date('Y-m-d H:i:s')
    ];
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (nhl_feed_is_enabled() && !nhl_feed_is_running()) {
        nhl_feed_start_worker();
    }
    goalhorn_json_response(200, nhl_feed_payload());
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    goalhorn_json_response(405, [
        'success' => false,
        'error' => 'Method not allowed',
        'timestamp' => date('Y-m-d H:i:s')
    ]);
}

$payload = json_decode(file_get_contents('php://input') ?: '{}', true);
if (!is_array($payload)) {
    $payload = $_POST;
}

$settings = nhl_feed_settings();
if (array_key_exists('source_team', $payload)) {
    $team = strtoupper((string) $payload['source_team']);
    if (!in_array($team, nhl_feed_valid_teams(), true)) {
        goalhorn_json_response(400, [
            'success' => false,
            'error' => 'Unsupported NHL team',
            'timestamp' => date('Y-m-d H:i:s')
        ]);
    }

    if ($team !== $settings['source_team']) {
        @unlink(NHL_FEED_STATE_FILE);
        $settings['source_team'] = $team;
        nhl_feed_write_settings($settings);
        goalhorn_log_activity('nhl_api_source_team_changed', 'NHL API source team changed to ' . $team);
    }
}

if (array_key_exists('enabled', $payload)) {
    $enabled = filter_var($payload['enabled'], FILTER_VALIDATE_BOOLEAN);
    nhl_feed_write_enabled($enabled);

    if ($enabled) {
        goalhorn_log_activity('nhl_api_feed_enabled', 'NHL API feed enabled from settings page');
        nhl_feed_start_worker();
        goalhorn_json_response(200, nhl_feed_payload('NHL API feed enabled'));
    }

    goalhorn_log_activity('nhl_api_feed_disabled', 'NHL API feed disabled from settings page');
    goalhorn_json_response(200, nhl_feed_payload('Manual buttons only'));
}

if (nhl_feed_is_enabled()) {
    nhl_feed_start_worker();
}

goalhorn_json_response(200, nhl_feed_payload('NHL API feed settings saved'));
?>
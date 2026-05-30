<?php
require_once __DIR__ . '/_helpers.php';

const BLUESGOAL_DATA_DIR = '/var/lib/bluesgoal';
const BLUESGOAL_RUN_DIR = '/run/bluesgoal';
const BLUESGOAL_LOG_DIR = '/var/log/bluesgoal';
const NHL_TEAMS_FILE = __DIR__ . '/../config/nhl_teams.json';

const NHL_FEED_ENABLED_FILE = BLUESGOAL_DATA_DIR . '/nhl_feed_enabled';
const NHL_FEED_SETTINGS_FILE = BLUESGOAL_DATA_DIR . '/nhl_feed_settings.json';
const NHL_FEED_STATUS_FILE = BLUESGOAL_RUN_DIR . '/nhl_feed_status.json';
const NHL_FEED_STATE_FILE = BLUESGOAL_DATA_DIR . '/nhl_feed_state.json';
const NHL_FEED_LOG = BLUESGOAL_LOG_DIR . '/nhl_feed.log';

const LEGACY_NHL_FEED_ENABLED_FILE = '/tmp/bluesgoal_nhl_feed_enabled';
const LEGACY_NHL_FEED_SETTINGS_FILE = '/tmp/bluesgoal_nhl_feed_settings.json';
const LEGACY_NHL_FEED_STATUS_FILE = '/tmp/bluesgoal_nhl_feed_status.json';
const LEGACY_NHL_FEED_STATE_FILE = '/tmp/bluesgoal_nhl_feed_state.json';

function nhl_feed_ensure_dir($dir) {
    if (is_dir($dir)) {
        return true;
    }
    return @mkdir($dir, 0775, true) || is_dir($dir);
}

function nhl_feed_ensure_runtime_dirs() {
    return nhl_feed_ensure_dir(BLUESGOAL_DATA_DIR)
        && nhl_feed_ensure_dir(BLUESGOAL_RUN_DIR)
        && nhl_feed_ensure_dir(BLUESGOAL_LOG_DIR);
}

function nhl_feed_migrate_legacy_file($newPath, $legacyPath) {
    if (file_exists($newPath) || !file_exists($legacyPath)) {
        return;
    }

    $dir = dirname($newPath);
    if (!nhl_feed_ensure_dir($dir)) {
        return;
    }

    @copy($legacyPath, $newPath);
}

function nhl_feed_migrate_legacy_files() {
    nhl_feed_migrate_legacy_file(NHL_FEED_ENABLED_FILE, LEGACY_NHL_FEED_ENABLED_FILE);
    nhl_feed_migrate_legacy_file(NHL_FEED_SETTINGS_FILE, LEGACY_NHL_FEED_SETTINGS_FILE);
    nhl_feed_migrate_legacy_file(NHL_FEED_STATUS_FILE, LEGACY_NHL_FEED_STATUS_FILE);
    nhl_feed_migrate_legacy_file(NHL_FEED_STATE_FILE, LEGACY_NHL_FEED_STATE_FILE);
}

function nhl_feed_team_map() {
    $decoded = json_decode((string) @file_get_contents(NHL_TEAMS_FILE), true);
    $teams = is_array($decoded) && isset($decoded['teams']) && is_array($decoded['teams'])
        ? $decoded['teams']
        : ['STL' => 'St. Louis Blues'];

    $normalized = [];
    foreach ($teams as $abbrev => $name) {
        $key = strtoupper(trim((string) $abbrev));
        if ($key !== '' && is_string($name)) {
            $normalized[$key] = $name;
        }
    }

    return $normalized ?: ['STL' => 'St. Louis Blues'];
}

function nhl_feed_valid_teams() {
    return array_keys(nhl_feed_team_map());
}

function nhl_feed_settings() {
    nhl_feed_migrate_legacy_files();

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

function nhl_feed_write_json_file($path, $payload, $pretty = false) {
    if (!nhl_feed_ensure_dir(dirname($path))) {
        return false;
    }

    $flags = $pretty ? JSON_PRETTY_PRINT : 0;
    return @file_put_contents($path, json_encode($payload, $flags), LOCK_EX) !== false;
}

function nhl_feed_write_settings($settings) {
    return nhl_feed_write_json_file(NHL_FEED_SETTINGS_FILE, $settings);
}

function nhl_feed_is_enabled() {
    nhl_feed_migrate_legacy_files();
    return file_exists(NHL_FEED_ENABLED_FILE) && trim((string) @file_get_contents(NHL_FEED_ENABLED_FILE)) === '1';
}

function nhl_feed_read_status() {
    nhl_feed_migrate_legacy_files();
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
    if (!nhl_feed_ensure_dir(dirname(NHL_FEED_ENABLED_FILE))) {
        return false;
    }
    return @file_put_contents(NHL_FEED_ENABLED_FILE, $enabled ? '1' : '0', LOCK_EX) !== false;
}

function nhl_feed_write_status($updates) {
    $status = nhl_feed_read_status();
    $status = array_merge($status, $updates, [
        'updated_at' => gmdate('c')
    ]);
    return nhl_feed_write_json_file(NHL_FEED_STATUS_FILE, $status, true);
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
    exec('sudo -n python3 -B -c ' . escapeshellarg('import sys') . ' 2>&1', $output, $exitCode);
    return $exitCode === 0 ? null : trim(implode("\n", $output));
}

function nhl_feed_start_worker() {
    nhl_feed_ensure_runtime_dirs();

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

    $command = 'nohup sudo -n python3 -B ' . escapeshellarg($script)
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
        'team_labels' => nhl_feed_team_map(),
        'message' => $message ?: ($enabled ? 'NHL API feed enabled' : 'Manual buttons only'),
        'data' => nhl_feed_read_status(),
        'timestamp' => date('Y-m-d H:i:s')
    ];
}

nhl_feed_migrate_legacy_files();

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
        if (!nhl_feed_write_settings($settings)) {
            goalhorn_json_response(500, [
                'success' => false,
                'error' => 'Unable to save NHL feed settings',
                'timestamp' => date('Y-m-d H:i:s')
            ]);
        }
        goalhorn_log_activity('nhl_api_source_team_changed', 'NHL API source team changed to ' . $team);
    }
}

if (array_key_exists('enabled', $payload)) {
    $enabled = filter_var($payload['enabled'], FILTER_VALIDATE_BOOLEAN);
    if (!nhl_feed_write_enabled($enabled)) {
        goalhorn_json_response(500, [
            'success' => false,
            'error' => 'Unable to save NHL feed enabled state',
            'timestamp' => date('Y-m-d H:i:s')
        ]);
    }

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

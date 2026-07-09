<?php
require_once __DIR__ . '/_helpers.php';

const MLB_TEAMS_FILE = __DIR__ . '/../config/mlb_teams.json';

define('BLUESGOAL_DATA_DIR', getenv('BLUESGOAL_DATA_DIR') ?: '/var/lib/bluesgoal');
define('BLUESGOAL_RUN_DIR', getenv('BLUESGOAL_RUN_DIR') ?: '/run/bluesgoal');
define('BLUESGOAL_LOG_DIR', getenv('BLUESGOAL_WORKER_LOG_DIR') ?: '/var/log/bluesgoal');

define('MLB_FEED_ENABLED_FILE', BLUESGOAL_DATA_DIR . '/mlb_feed_enabled');
define('MLB_FEED_SETTINGS_FILE', BLUESGOAL_DATA_DIR . '/mlb_feed_settings.json');
define('MLB_FEED_STATUS_FILE', BLUESGOAL_RUN_DIR . '/mlb_feed_status.json');
define('MLB_FEED_STATE_FILE', BLUESGOAL_DATA_DIR . '/mlb_feed_state.json');
define('MLB_FEED_LOG', BLUESGOAL_LOG_DIR . '/mlb_feed.log');

function mlb_feed_ensure_dir($dir) {
    if (is_dir($dir)) {
        return true;
    }
    return @mkdir($dir, 0775, true) || is_dir($dir);
}

function mlb_feed_ensure_runtime_dirs() {
    return mlb_feed_ensure_dir(BLUESGOAL_DATA_DIR)
        && mlb_feed_ensure_dir(BLUESGOAL_RUN_DIR)
        && mlb_feed_ensure_dir(BLUESGOAL_LOG_DIR);
}

function mlb_feed_team_map() {
    $decoded = json_decode((string) @file_get_contents(MLB_TEAMS_FILE), true);
    $teams = is_array($decoded) && isset($decoded['teams']) && is_array($decoded['teams'])
        ? $decoded['teams']
        : ['138' => 'St. Louis Cardinals'];

    $normalized = [];
    foreach ($teams as $id => $name) {
        $key = trim((string) $id);
        if ($key !== '' && ctype_digit($key) && is_string($name)) {
            $normalized[$key] = $name;
        }
    }

    return $normalized ?: ['138' => 'St. Louis Cardinals'];
}

function mlb_feed_valid_teams() {
    return array_keys(mlb_feed_team_map());
}

function mlb_feed_settings() {
    $settings = [];
    if (file_exists(MLB_FEED_SETTINGS_FILE)) {
        $decoded = json_decode((string) @file_get_contents(MLB_FEED_SETTINGS_FILE), true);
        if (is_array($decoded)) {
            $settings = $decoded;
        }
    }

    $team = (string) ($settings['source_team'] ?? '138');
    if (!in_array($team, mlb_feed_valid_teams(), true)) {
        $team = '138';
    }

    return ['source_team' => $team];
}

function mlb_feed_write_json_file($path, $payload, $pretty = false) {
    if (!mlb_feed_ensure_dir(dirname($path))) {
        return false;
    }

    $flags = $pretty ? JSON_PRETTY_PRINT : 0;
    return @file_put_contents($path, json_encode($payload, $flags), LOCK_EX) !== false;
}

function mlb_feed_write_settings($settings) {
    return mlb_feed_write_json_file(MLB_FEED_SETTINGS_FILE, $settings);
}

function mlb_feed_is_enabled() {
    return file_exists(MLB_FEED_ENABLED_FILE) && trim((string) @file_get_contents(MLB_FEED_ENABLED_FILE)) === '1';
}

function mlb_feed_read_status() {
    if (!file_exists(MLB_FEED_STATUS_FILE)) {
        return [];
    }

    $decoded = json_decode((string) @file_get_contents(MLB_FEED_STATUS_FILE), true);
    return is_array($decoded) ? $decoded : [];
}

function mlb_feed_script_path() {
    return __DIR__ . '/mlb_feed/mlb_feed.py';
}

function mlb_feed_is_running() {
    $script = mlb_feed_script_path();
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

function mlb_feed_write_enabled($enabled) {
    if (!mlb_feed_ensure_dir(dirname(MLB_FEED_ENABLED_FILE))) {
        return false;
    }
    return @file_put_contents(MLB_FEED_ENABLED_FILE, $enabled ? '1' : '0', LOCK_EX) !== false;
}

function mlb_feed_wait_for_worker_stop($seconds = 5) {
    $deadline = microtime(true) + $seconds;
    while (mlb_feed_is_running() && microtime(true) < $deadline) {
        usleep(250000);
    }
}

function mlb_feed_write_status($updates) {
    $status = mlb_feed_read_status();
    $status = array_merge($status, $updates, [
        'updated_at' => gmdate('c')
    ]);
    return mlb_feed_write_json_file(MLB_FEED_STATUS_FILE, $status, true);
}

function mlb_feed_recent_start_attempt($seconds = 30) {
    $status = mlb_feed_read_status();
    if (empty($status['last_worker_start_attempt_at'])) {
        return false;
    }

    $attemptAt = strtotime((string) $status['last_worker_start_attempt_at']);
    return $attemptAt !== false && (time() - $attemptAt) < $seconds;
}

function mlb_feed_worker_sudo_error() {
    $output = [];
    $exitCode = 0;
    exec('sudo -n python3 -B -c ' . escapeshellarg('import sys') . ' 2>&1', $output, $exitCode);
    return $exitCode === 0 ? null : trim(implode("\n", $output));
}

function mlb_feed_start_worker() {
    mlb_feed_ensure_runtime_dirs();

    if (mlb_feed_is_running()) {
        return true;
    }

    if (mlb_feed_recent_start_attempt()) {
        return false;
    }

    $script = mlb_feed_script_path();
    if (!file_exists($script)) {
        mlb_feed_write_status([
            'enabled' => mlb_feed_is_enabled(),
            'running' => false,
            'message' => 'MLB feed worker script not found',
            'last_error' => 'Missing worker script: ' . $script,
            'current_poll_seconds' => null,
            'last_worker_start_attempt_at' => gmdate('c')
        ]);
        return false;
    }

    $sudoError = mlb_feed_worker_sudo_error();
    if ($sudoError !== null) {
        mlb_feed_write_status([
            'enabled' => true,
            'running' => false,
            'message' => 'MLB feed worker cannot start',
            'last_error' => $sudoError,
            'current_poll_seconds' => null,
            'last_worker_start_attempt_at' => gmdate('c')
        ]);
        return false;
    }

    mlb_feed_write_status([
        'enabled' => true,
        'running' => false,
        'message' => 'Starting MLB feed worker',
        'last_error' => null,
        'current_poll_seconds' => null,
        'last_worker_start_attempt_at' => gmdate('c')
    ]);

    $command = 'BLUESGOAL_DATA_DIR=' . escapeshellarg(BLUESGOAL_DATA_DIR)
        . ' BLUESGOAL_RUN_DIR=' . escapeshellarg(BLUESGOAL_RUN_DIR)
        . ' BLUESGOAL_WORKER_LOG_DIR=' . escapeshellarg(BLUESGOAL_LOG_DIR)
        . ' nohup python3 -B ' . escapeshellarg($script)
        . ' >> ' . escapeshellarg(MLB_FEED_LOG)
        . ' 2>&1 &';
    @shell_exec($command);
    sleep(1);

    if (mlb_feed_is_running()) {
        mlb_feed_write_status([
            'enabled' => true,
            'running' => true,
            'message' => 'MLB feed worker started',
            'last_error' => null
        ]);
        return true;
    }

    mlb_feed_write_status([
        'enabled' => true,
        'running' => false,
        'message' => 'MLB feed worker failed to start',
        'last_error' => 'Worker process was not found after launch; check ' . MLB_FEED_LOG
    ]);
    return false;
}

function mlb_feed_payload($message = null) {
    $enabled = mlb_feed_is_enabled();
    return [
        'success' => true,
        'enabled' => $enabled,
        'running' => mlb_feed_is_running(),
        'settings' => mlb_feed_settings(),
        'teams' => mlb_feed_valid_teams(),
        'team_labels' => mlb_feed_team_map(),
        'message' => $message ?: ($enabled ? 'MLB run trigger enabled' : 'MLB run trigger off'),
        'data' => mlb_feed_read_status(),
        'timestamp' => date('Y-m-d H:i:s')
    ];
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (mlb_feed_is_enabled() && !mlb_feed_is_running()) {
        mlb_feed_start_worker();
    }
    goalhorn_json_response(200, mlb_feed_payload());
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

$settings = mlb_feed_settings();
if (array_key_exists('source_team', $payload)) {
    $team = (string) $payload['source_team'];
    if (!in_array($team, mlb_feed_valid_teams(), true)) {
        goalhorn_json_response(400, [
            'success' => false,
            'error' => 'Unsupported MLB team',
            'timestamp' => date('Y-m-d H:i:s')
        ]);
    }

    if ($team !== $settings['source_team']) {
        @unlink(MLB_FEED_STATE_FILE);
        $settings['source_team'] = $team;
        if (!mlb_feed_write_settings($settings)) {
            goalhorn_json_response(500, [
                'success' => false,
                'error' => 'Unable to save MLB feed settings',
                'timestamp' => date('Y-m-d H:i:s')
            ]);
        }
        goalhorn_log_activity('mlb_api_source_team_changed', 'MLB run trigger source team changed to ' . $team);
    }
}

if (array_key_exists('enabled', $payload)) {
    $enabled = filter_var($payload['enabled'], FILTER_VALIDATE_BOOLEAN);
    if (!mlb_feed_write_enabled($enabled)) {
        goalhorn_json_response(500, [
            'success' => false,
            'error' => 'Unable to save MLB feed enabled state',
            'timestamp' => date('Y-m-d H:i:s')
        ]);
    }

    if ($enabled) {
        goalhorn_log_activity('mlb_api_feed_enabled', 'MLB run trigger enabled from settings page');
        mlb_feed_start_worker();
        goalhorn_json_response(200, mlb_feed_payload('MLB run trigger enabled'));
    }

    goalhorn_log_activity('mlb_api_feed_disabled', 'MLB run trigger disabled from settings page');
    mlb_feed_wait_for_worker_stop();
    goalhorn_json_response(200, mlb_feed_payload('MLB run trigger off'));
}

if (mlb_feed_is_enabled()) {
    mlb_feed_start_worker();
}

goalhorn_json_response(200, mlb_feed_payload('MLB run trigger settings saved'));
?>

<?php
require_once __DIR__ . '/_helpers.php';

const NHL_FEED_ENABLED_FILE = '/tmp/bluesgoal_nhl_feed_enabled';
const NHL_FEED_STATUS_FILE = '/tmp/bluesgoal_nhl_feed_status.json';
const NHL_FEED_SCRIPT = '/var/www/html/goalhorn/nhl_feed/nhl_feed.py';
const NHL_FEED_LOG = '/tmp/bluesgoal_nhl_feed.log';

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

function nhl_feed_is_running() {
    $output = [];
    $exitCode = 1;
    exec('pgrep -f ' . escapeshellarg('goalhorn/nhl_feed/nhl_feed.py'), $output, $exitCode);
    return $exitCode === 0 && count($output) > 0;
}

function nhl_feed_write_enabled($enabled) {
    @file_put_contents(NHL_FEED_ENABLED_FILE, $enabled ? '1' : '0', LOCK_EX);
}

function nhl_feed_start_worker() {
    if (nhl_feed_is_running()) {
        return;
    }

    $command = 'nohup sudo python3 ' . escapeshellarg(NHL_FEED_SCRIPT)
        . ' >> ' . escapeshellarg(NHL_FEED_LOG)
        . ' 2>&1 &';
    @shell_exec($command);
}

function nhl_feed_payload($message = null) {
    $enabled = nhl_feed_is_enabled();
    return [
        'success' => true,
        'enabled' => $enabled,
        'running' => nhl_feed_is_running(),
        'message' => $message ?: ($enabled ? 'NHL API feed enabled' : 'Manual buttons only'),
        'data' => nhl_feed_read_status(),
        'timestamp' => date('Y-m-d H:i:s')
    ];
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
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

$enabled = filter_var($payload['enabled'] ?? false, FILTER_VALIDATE_BOOLEAN);
nhl_feed_write_enabled($enabled);

if ($enabled) {
    goalhorn_log_activity('nhl_api_feed_enabled', 'NHL API feed enabled from web UI');
    nhl_feed_start_worker();
    goalhorn_json_response(200, nhl_feed_payload('NHL API feed enabled'));
}

goalhorn_log_activity('nhl_api_feed_disabled', 'NHL API feed disabled from web UI');
goalhorn_json_response(200, nhl_feed_payload('Manual buttons only'));
?>
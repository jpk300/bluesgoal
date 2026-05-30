<?php
/**
 * Shared helpers for goalhorn JSON endpoints.
 */

const GOALHORN_RUN_DIR = '/run/bluesgoal';
const GOALHORN_ACTION_LOCK_FILE = GOALHORN_RUN_DIR . '/action.lock';

function goalhorn_ensure_run_dir() {
    if (is_dir(GOALHORN_RUN_DIR)) {
        return true;
    }
    return @mkdir(GOALHORN_RUN_DIR, 0775, true) || is_dir(GOALHORN_RUN_DIR);
}

function goalhorn_json_response($statusCode, $payload) {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    header('Cache-Control: no-store');
    echo json_encode($payload);
    exit;
}

function goalhorn_log_activity($action, $message) {
    $command = 'python3 /var/www/html/log_activity.py '
        . escapeshellarg($action) . ' '
        . escapeshellarg($message)
        . ' 2>/dev/null &';
    @shell_exec($command);
}

function goalhorn_run_python_action($action, $message, $scriptPath, $useLock = true) {
    if (!file_exists($scriptPath)) {
        goalhorn_log_activity($action, 'Script not found: ' . $scriptPath);
        goalhorn_json_response(500, [
            'success' => false,
            'error' => 'Action script not found',
            'timestamp' => date('Y-m-d H:i:s')
        ]);
    }

    $lockHandle = null;
    if ($useLock) {
        if (!goalhorn_ensure_run_dir()) {
            goalhorn_json_response(500, [
                'success' => false,
                'error' => 'Unable to create runtime directory for action lock',
                'timestamp' => date('Y-m-d H:i:s')
            ]);
        }

        $lockHandle = fopen(GOALHORN_ACTION_LOCK_FILE, 'c');
        if (!$lockHandle) {
            goalhorn_json_response(500, [
                'success' => false,
                'error' => 'Unable to create action lock',
                'timestamp' => date('Y-m-d H:i:s')
            ]);
        }

        if (!flock($lockHandle, LOCK_EX | LOCK_NB)) {
            goalhorn_json_response(409, [
                'success' => false,
                'error' => 'Another action is already running',
                'retry_after' => 2,
                'timestamp' => date('Y-m-d H:i:s')
            ]);
        }
    }

    goalhorn_log_activity($action, $message);

    $outputLines = [];
    $exitCode = 0;
    $command = 'sudo python3 ' . escapeshellarg($scriptPath) . ' 2>&1';
    exec($command, $outputLines, $exitCode);

    if ($lockHandle) {
        flock($lockHandle, LOCK_UN);
        fclose($lockHandle);
    }

    $output = trim(implode("\n", $outputLines));
    if ($exitCode !== 0) {
        goalhorn_log_activity($action . '_error', $output ?: 'Exit code ' . $exitCode);
        goalhorn_json_response(500, [
            'success' => false,
            'error' => 'Action failed',
            'details' => $output,
            'timestamp' => date('Y-m-d H:i:s')
        ]);
    }

    goalhorn_json_response(200, [
        'success' => true,
        'message' => $message,
        'output' => $output,
        'timestamp' => date('Y-m-d H:i:s')
    ]);
}
?>

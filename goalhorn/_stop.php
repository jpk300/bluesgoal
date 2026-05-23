<?php
/**
 * Stop Audio Endpoint
 * Stops any currently playing audio
 */

header('Content-Type: application/json');

$PYTHON_SCRIPT = '/var/www/html/goalhorn/stop/stop_master.py';

// Log activity
@shell_exec('python3 /var/www/html/log_activity.py stop "Triggered from web UI" 2>/dev/null &');

// Execute the stop script
$output = shell_exec('sudo python3 ' . escapeshellarg($PYTHON_SCRIPT) . ' 2>&1');

if ($output === null) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Failed to execute stop command'
    ]);
    exit;
}

http_response_code(200);
echo json_encode([
    'success' => true,
    'message' => 'Audio stopped',
    'timestamp' => date('Y-m-d H:i:s')
]);
?>

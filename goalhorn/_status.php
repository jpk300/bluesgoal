<?php
/**
 * Status endpoint for current audio and volume state.
 */

header('Content-Type: application/json');
header('Cache-Control: no-store');

$PYTHON_SCRIPT = '/var/www/html/goalhorn/status/status.py';
$output = shell_exec('python3 ' . escapeshellarg($PYTHON_SCRIPT) . ' 2>&1');

if ($output === null) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Failed to read status',
        'timestamp' => date('Y-m-d H:i:s')
    ]);
    exit;
}

echo $output;
?>

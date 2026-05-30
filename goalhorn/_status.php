<?php
/**
 * Status endpoint for current audio and volume state.
 */

header('Content-Type: application/json');
header('Cache-Control: no-store');

require_once __DIR__ . '/_helpers.php';

$PYTHON_SCRIPT = goalhorn_path('goalhorn/status/status.py');
$output = shell_exec('sudo -n python3 -B ' . escapeshellarg($PYTHON_SCRIPT) . ' 2>&1');

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

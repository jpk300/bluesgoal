<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_run_python_action(
    'stop',
    'Audio stopped',
    '/var/www/html/goalhorn/stop/stop_master.py',
    false
);
?>

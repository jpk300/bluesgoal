<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_require_post();

goalhorn_run_python_action(
    'stop',
    'Audio stopped',
    goalhorn_path('goalhorn/stop/stop_master.py'),
    false
);
?>

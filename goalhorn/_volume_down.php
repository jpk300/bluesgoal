<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_run_python_action(
    'volume_down',
    'Volume decreased',
    '/var/www/html/goalhorn/volume/volume_down_master.py',
    false
);
?>

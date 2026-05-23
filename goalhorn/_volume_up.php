<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_run_python_action(
    'volume_up',
    'Volume increased',
    '/var/www/html/goalhorn/volume/volume_up_master.py',
    false
);
?>

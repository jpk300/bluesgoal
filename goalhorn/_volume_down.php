<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_require_post();

goalhorn_run_python_action(
    'volume_down',
    'Volume decreased',
    goalhorn_path('goalhorn/volume/volume_down_master.py'),
    false
);
?>

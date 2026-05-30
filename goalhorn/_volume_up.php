<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_require_post();

goalhorn_run_python_action(
    'volume_up',
    'Volume increased',
    goalhorn_path('goalhorn/volume/volume_up_master.py'),
    false
);
?>

<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_run_python_action(
    'powerplay',
    'Power Play started',
    '/var/www/html/goalhorn/powerplay/powerplay.py',
    true
);
?>

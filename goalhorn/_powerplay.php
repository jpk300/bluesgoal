<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_run_python_action(
    'powerplay',
    'Power Play has finished',
    '/var/www/html/goalhorn/action_runner.py',
    true,
    ['powerplay']
);
?>

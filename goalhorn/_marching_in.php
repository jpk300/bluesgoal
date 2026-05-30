<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_require_post();

goalhorn_run_python_action(
    'marching_in',
    'Marching In has finished',
    goalhorn_path('goalhorn/action_runner.py'),
    true,
    ['marching_in']
);
?>

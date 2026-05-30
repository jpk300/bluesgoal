<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_require_post();

goalhorn_run_python_action(
    'bluesgoal_oldschool',
    'Old School goal horn has finished',
    goalhorn_path('goalhorn/action_runner.py'),
    true,
    ['bluesgoal_oldschool']
);
?>

<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_run_python_action(
    'bluesgoal_winterclassic',
    'Winter Classic goal horn has finished',
    '/var/www/html/goalhorn/bluesgoal_winterclassic/bluesgoal_winterclassic_master.py',
    true
);
?>

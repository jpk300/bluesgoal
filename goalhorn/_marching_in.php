<?php
require_once __DIR__ . '/_helpers.php';

goalhorn_run_python_action(
    'marching_in',
    'Marching In started',
    '/var/www/html/goalhorn/marching_in/marching_in.py',
    true
);
?>

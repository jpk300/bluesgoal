<?php
header('Location: http://bluesgoal.home.local');
$output = shell_exec('sudo python /var/www/html/goalhorn/marching_in_playoffs/marching_in_playoffs.py');
echo "<pre>$output</pre>";
?>
$output = shell_exec('http://bluesgoal.home.local');


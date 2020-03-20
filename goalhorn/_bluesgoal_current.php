<?php
header('Location: http://bluesgoal.home.local');
$output = shell_exec('sudo python /var/www/html/goalhorn/bluesgoal_current/bluesgoal_current_master.py');
echo "<pre>$output</pre>";
?>
$output = shell_exec('http://bluesgoal.home.local');


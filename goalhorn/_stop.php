<?php
header('Location: http://bluesgoal.home.local');
$output = shell_exec('sudo python /var/www/html/goalhorn/stop/stop_master.py');
echo "<pre>$output</pre>";
?>

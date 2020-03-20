<?php
header('Location: http://bluesgoal.home.local');
$output = shell_exec('sudo python /var/www/html/goalhorn/volume/volume_down_master.py');
echo "<pre>$output</pre>";	
?>

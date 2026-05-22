import os
import alsaaudio

#volume = "amixer get PCM | awk '$0~/%/{print $4}' | tr -d '[]%'"
#print (volume)

#os.system('amixer set PCM -- 90%')

m = alsaaudio.Mixer('PCM')
vol = m.getvolume()
vol = int(vol[0])

newVol = vol+5

if newVol <=100:
	m.setvolume(newVol) 
else:
	exit

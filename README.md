# vp9-encode ✨
Makes encoding vp9 with ffmpeg way more user-friendly. \
Uses google-recommended encoder settings, has the ability to auto-crop black borders and fixes libopus (side)-channel bug.

## Example (using interactive.py)
```
$ python3 interactive.py
Universal 4k/2k/1080p/720p 24/25/30fps vp9 encoding guide
Input video file:
> "mkv/Revenge of the Sith_t01.mkv"
Output file: (optional)
> "webm/i-have-the-high-ground.webm"
Start (00:00:00): (optional)
> 01:59:19
End (00:00:00): (optional)
> 01:59:28
Languages to include: (eng,deu,... ,empty for all)
> eng
Crop video? (y/n)
> y
Multithread? (y/n)
> n
Two-pass encoding? (y/n)
> y
Niceness (19=low priority, -20=high priority):
> 19
> config:
	in:  mkv/Revenge of the Sith_t01.mkv
	out: webm/i-have-the-high-ground.webm
	start: 01:59:19
	end: 01:59:28
	lang: ['eng']
	nice: 19
	autocrop: True
	multithread: False
	twopass: True
loading metadata...
> metadata:
	res: 1920x1072
	codec: h264
	audio streams:
		[index] language : sample_fmt : sample_rate : layout
		[1] eng : fltp : 48000 : stereo
		[2] eng : fltp : 48000 : 5.1
using profile 2 (1080p)
including audio streams: 1,2
running cropdetect...
    crop=1920:816:0:128
using 1 thread(s)
encoding... (1st pass)
frame=  270 fps= 29 q=0.0 Lsize=N/A time=00:00:00.00 bitrate=N/A speed=   0x    
encoding... (2nd pass)
    [...]
```

## Example (using vp9encode.py)
```
vp9encode usage:

parameters:
-i, --in          : input file (required)
-o, --out         : output file (.webm, optional)
-l, --lang        : languages to include (eng,deu...; optional)
-s, --start       : start (00:00:00, optional)
-e, --end         : end (00:00:00, optional)
-n, --nice        : niceness (19=low priority, -20=high priority, optional)

flags:
-c, --crop        : autocrop black borders
-m, --multithread : enable multithreading
-t, --twopass     : use two-pass encoding

e.g.
./vp9encode.py -i "mkv/Revenge of the Sith_t01.mkv" -o "webm/i-have-the-high-ground.webm" -s 01:59:19 -e 01:59:28 -n 19 -c -t
```

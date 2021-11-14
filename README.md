# vp9-encode ✨
Makes encoding vp9 with ffmpeg waay more user-friendly. \
Uses google-recommended two pass encoding, auto-crops black borders and fixes libopus (side)-channel bug.

## Example
```
$ python3 vp9-encode.py
Universal 1080p 24/25/30fps vp9 encoding guide

Video file:
> "Attack of the Clones_t01.mkv"

Choose audio streams: (comma separated, optional)
[index] language : channels : sample_fmt : sample_rate : hearing_impaired? : visual_impaired?
[1] eng : Surround 5.1 : fltp : 48000 : 0 : 0
[2] spa : Surround 5.1 : fltp : 48000 : 0 : 0
[3] spa : Surround 5.1 : fltp : 48000 : 0 : 0
[4] deu : Surround 5.1 : s32p : 48000 : 0 : 0
[5] deu : Surround 5.1 : fltp : 48000 : 0 : 0
[6] hun : Surround 5.1 : fltp : 48000 : 0 : 0
[7] pol : Surround 5.1 : fltp : 48000 : 0 : 0
[8] eng : Stereo : fltp : 48000 : 0 : 0
[9] eng : Stereo : fltp : 48000 : 0 : 0
> 1,5

Start (00:00:00): (optional)
> 

End (00:00:00): (optional)
> 00:30:00

Crop detection timestamp:
> 00:06:33

Output file: (optional)
> star-wars-attack-of-the-clones.webm

Threads:
> 2

Niceness (19=low priority, -20=high priority):
> 19

Encoding... (1st pass)
frame=  512 fps= 29 q=0.0 Lsize=N/A time=00:00:00.00 bitrate=N/A speed=   0x    
Encoding... (2nd pass)
frame=   324 fps= 17 q=0.0 Lsize=     179kB time=00:00:02.65 bitrate= 553.6kbits/s speed=0.817x 
```

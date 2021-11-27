# vp9-encode ✨
Makes encoding vp9 with ffmpeg waay more user-friendly. \
Uses google-recommended two pass encoding, crops black borders and fixes libopus (side)-channel bug.

## Example
```
$ python3 vp9-encode.py
Universal 1080p 24/25/30fps vp9 encoding guide
Video file:
> "mkv/Revenge of the Sith_t01.mkv"
Choose audio streams: (comma separated, optional)
[index] language : channels : sample_fmt : sample_rate : hearing_impaired? : visual_impaired?
[1] eng : fltp : 48000 : ? : ?
[2] spa : fltp : 48000 : ? : ?
[3] spa : fltp : 48000 : ? : ?
[4] deu : s32p : 48000 : ? : ?
[5] deu : fltp : 48000 : ? : ?
[6] hun : fltp : 48000 : ? : ?
[7] pol : fltp : 48000 : ? : ?
[8] eng : fltp : 48000 : ? : ?
[9] eng : fltp : 48000 : ? : ?
> 1,5
Start (00:00:00): (optional)
> 01:59:19
End (00:00:00): (optional)
> 01:59:28
Crop detection timestamp: (optional)
> 00:45:23
detected crop=1904:800:8:140
> is this crop ok? (y/n): n
Crop detection timestamp: (optional)
00:35:45
detected crop=1904:816:8:132
> is this crop ok? (y/n): y
Output file: (optional)
> "webm/i-have-the-high-ground.webm"
Threads:
> 4
Niceness (19=low priority, -20=high priority):
> 19
Encoding... (1st pass)
frame=  270 fps= 29 q=0.0 Lsize=N/A time=00:00:00.00 bitrate=N/A speed=   0x    
Encoding... (2nd pass)
    [...]
```

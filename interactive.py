#!/usr/bin/env python3
import vp9encode

if __name__ == '__main__':
    print("Universal 4k/2k/1080p/720p 24/25/30fps vp9 encoding guide")
    f_in = input("Input video file:\n").replace("\"", "").replace("\'", "")

    f_out = input("Output file: (optional)\n").replace("\"", "").replace("\'", "")

    start = input("Start (00:00:00): (optional)\n")

    end = input("End (00:00:00): (optional)\n")

    lang = input("Languages to include: (eng,deu,... ,empty for all)\n")

    crop = input("Crop video? (y/n)\n") == "y"

    multithread = input("Multithread? (y/n)\n") == "y"

    twopass = input("Two-pass encoding? (y/n)\n") == "y"

    nice = input("Niceness (19=low priority, -20=high priority):\n")

    conf = vp9encode.Config(f_in=f_in, f_out=f_out, start=start, end=end, crop=crop, nice=nice,
                            lang=lang, multithread=multithread, twopass=twopass)
    vp9encode.print_config(conf)
    vp9encode.encode(conf)

#!/usr/bin/env python3
import getopt
import json
import os
import sys

#  @formatter:off   libvpx-vp9 encoder parameters (@ 24,25,30 fps)
# profile                  0        1        2        3
height =            [    2160,    1440,    1080,     720]
avgrate =           ["12000k", "6000k", "1800k", "1024k"]
minrate =           [ "6000k", "3000k",  "900k",  "512k"]
maxrate =           ["17400k", "8700k", "2610k", "1485k"]
crf =               [      15,      24,       31,     32]
quality =           [  "good",  "good",   "good", "good"]
tile_columns =      [       3,       3,        2,      2]
g =                 [     240,     240,      240,    240]
first_pass_speed =  [       4,       4,        4,      4]
second_pass_speed = [       2,       2,        2,      2]
# @formatter:on


def print_usage(code):
    print("-----vp9-encode-usage----\n")
    exit(code)


class Config:
    def __init__(self, argv):
        self.f_in = ""
        self.f_out = ""
        self.start = ""
        self.end = ""
        self.lang = []
        self.crop = False
        self.multithread = False
        if not 1 <= len(argv):
            print_usage(1)

        try:
            opts, args = getopt.getopt(argv, "i:o:l:s:e:cm",
                                       ["in=", "out=", "lang=", "start=", "end=", "crop", "multithread"])
        except getopt.GetoptError:
            print_usage(1)
        for opt, arg in opts:
            if opt in ("-i", "--in"):
                self.f_in = str(arg)
            elif opt in ("-o", "--out"):
                self.f_out = str(arg)
            elif opt in ("-l", "--lang"):
                self.lang = arg.lower().split(",")
            elif opt in ("-s", "--start"):
                self.start = f"-ss {arg}"
            elif opt in ("-e", "--end"):
                self.end = f"-to {arg}"
            elif opt in ("-c", "--crop"):
                self.crop = True
            elif opt in ("-m", "--multithread"):
                self.multithread = True

        if self.f_in == "":
            print_usage(1)

        if self.f_out == "":
            self.f_out = os.path.splitext(self.f_in)[0] + ".webm"

    def print(self):
        print(f"--config--\n\tin:  {self.f_in}\n\tout: {self.f_out}\n\tautocrop: {self.crop}")


class Metadata:
    def __init__(self, path):
        all_streams = json.load(os.popen(f"ffprobe -hide_banner -show_streams -print_format json {path} 2>/dev/null"))
        self.audio_streams = [stream for stream in all_streams["streams"] if stream["codec_type"] == "audio"]
        video_stream = all_streams["streams"][0]
        self.codec = video_stream["codec_name"]
        self.width = int(video_stream["width"])
        self.height = int(video_stream["height"])
        self.duration_min = float(video_stream["duration"]) / 60.0

    def print(self):
        print(f"--metadata--\n\tres: {self.width}x{self.height}\n\tcodec: {self.codec}\n\tduration: {int(self.duration_min)} min")
        print("\taudio streams:\n\t\t[index] language : channels : sample_fmt : sample_rate : hearing_impaired? : "
              "visual_impaired?")
        for stream in self.audio_streams:
            print("\t\t[%d] %s : %s : %s : %s : %s" % (
                stream['index'], stream['tags'].get('language'),
                stream['sample_fmt'], stream['sample_rate'],
                stream['disposition'].get('hearing_impaired') or "?",
                stream['disposition'].get('visual_impaired') or "?"
            ))

    def determine_profile_index(self):
        p = -1
        k = 1_000_000
        for i in range(len(height)):
            t = abs(height[i] - self.height)
            if t <= k:
                p = i
                k = t
        return p


if __name__ == "__main__":
    conf = Config(sys.argv[1:])
    conf.print()

    meta = Metadata(conf.f_in)
    meta.print()

    p = meta.determine_profile_index()

    print("--------------------------")
    print(f"> using profile {p} ({height[p]}p)")

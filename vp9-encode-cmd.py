#!/usr/bin/env python3
import getopt
import json
import os
import sys

#  @formatter:off   libvpx-vp9 encoder parameters (@ 24,25,30 fps)
# profile                  0        1        2        3
width =             [    3860,    2560,    1920,    1280]
height =            [    2160,    1440,    1080,     720]
avgrate =           ["12000k", "6000k", "1800k", "1024k"]
minrate =           [ "6000k", "3000k",  "900k",  "512k"]
maxrate =           ["17400k", "8700k", "2610k", "1485k"]
audiorate =         [  "160k",  "128k",  "128k",   "96k"]
crf =               [      15,      24,       31,     32]
quality =           [  "good",  "good",   "good", "good"]
tile_columns =      [       3,       3,        2,      2]
g =                 [     240,     240,      240,    240]
first_pass_speed =  [       4,       4,        4,      4]
second_pass_speed = [       2,       2,        2,      2]
# @formatter:on


def print_usage(code):
    print("-----vp9-encode-usage----\n")
    # todo
    exit(code)


class Config:
    def __init__(self, argv):
        self.f_in = ""
        self.f_out = ""
        self.start = ""
        self.end = ""
        self.lang = []
        self.nice = 19
        self.crop = False
        self.multithread = False
        self.twopass = False
        if not 1 <= len(argv):
            print_usage(1)

        try:
            opts, args = getopt.getopt(argv, "i:o:l:s:e:n:cmt",
                                       ["in=", "out=", "lang=", "start=", "end=", "nice=", "crop", "multithread", "twopass"])
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
                self.start = str(arg)
            elif opt in ("-e", "--end"):
                self.end = str(arg)
            elif opt in ("-n", "--nice"):
                self.nice = int(arg)
            elif opt in ("-c", "--crop"):
                self.crop = True
            elif opt in ("-m", "--multithread"):
                self.multithread = True
            elif opt in ("-t", "--twopass"):
                self.twopass = True

        if self.f_in == "":
            print_usage(1)

        if self.f_out == "":
            self.f_out = os.path.splitext(self.f_in)[0] + ".webm"

    def print(self):
        print(f"--config--\n\tin:  {self.f_in}\n\tout: {self.f_out}\n\tautocrop: {self.crop}")


class Metadata:
    def __init__(self, path):
        self.path = path
        with os.popen(f"ffprobe -hide_banner -show_streams -print_format json '{path}' 2>/dev/null") as meta_json:
            all_streams = json.load(meta_json)
        self.audio_streams = [stream for stream in all_streams["streams"] if stream["codec_type"] == "audio"]
        video_stream = [stream for stream in all_streams["streams"] if stream["codec_type"] == "video"][0]
        self.codec = video_stream["codec_name"]
        self.width = int(video_stream["width"])
        self.height = int(video_stream["height"])

    def print(self):
        print(
            f"--metadata--\n\tres: {self.width}x{self.height}\n\tcodec: {self.codec}")
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
        d = 1_000_000
        for i in range(len(height)):
            t = ((width[i] - self.width) ** 2 + (height[i] - self.height) ** 2) ** 0.5
            if t <= d:
                p = i
                d = t
        return p

    def filter_audio_streams(self, lang):
        if len(lang) == 0 or len(self.audio_streams) == 1:
            return self.audio_streams
        return [stream for stream in self.audio_streams if stream["tags"].get("language") in lang]

    def determine_crop(self):
        crop = os.popen(
            f"nice -n 19 ffmpeg -ss 600 -i {self.path}" + " -t 120 -vsync vfr -vf cropdetect -f null - 2>&1"
                                       " | awk '/crop/ { print $NF }' | tail -1").readline().removesuffix("\n")
        return crop


def generate_ffmpeg_complex_audio_filter(streams):
    fix_libopus_cl = {"5.0(side)": "5.0", "5.1(side)": "5.1"}  # fix libopus inability to encode (side)-channels
    maps = ["[:%d]channelmap=channel_layout='%s'" % (stream["index"], fix_libopus_cl[stream["channel_layout"]])
            if stream.get("channel_layout") in fix_libopus_cl.keys() else "[:%d]anull" % (stream["index"])
            for stream in streams]
    complex_filter = ";".join(maps)
    if complex_filter != "":
        complex_filter = f"-filter_complex \"{complex_filter}\""
    maps = ["-metadata:s:a:%d language=\"%s\" -metadata:s:a:%d title=\"%s\""
            % (i, stream['tags'].get('language'), i, stream['tags'].get('title'))
            for i, stream in enumerate(streams)]
    metadata = " ".join(maps)
    return f"{complex_filter} {metadata}"


if __name__ == "__main__":
    conf = Config(sys.argv[1:])
    conf.print()

    meta = Metadata(conf.f_in)
    meta.print()

    print("--------------------------")
    p = meta.determine_profile_index()
    print(f"> using profile {p} ({height[p]}p)")

    a = meta.filter_audio_streams(conf.lang)
    if len(a) == 0:
        print(f"> no audio streams found matching {conf.lang}, including all")
        a = meta.audio_streams
    else:
        print(f"> including audio streams: " + ",".join([str(stream["index"]) for stream in a]))
    arg_complex_filter = generate_ffmpeg_complex_audio_filter(a)

    arg_crop = ""
    if conf.crop:
        print("> running cropdetect...")
        arg_crop = meta.determine_crop()
        print(f"\t{arg_crop}")
        arg_crop = f"-vf {arg_crop}"

    arg_threads = 1
    arg_tile_columns = 0
    arg_row_mt = 0
    if conf.multithread:
        arg_row_mt = 1
        arg_tile_columns = tile_columns[p]
        arg_threads = tile_columns[p] * 4
        print(f"> using {arg_threads} threads")

    arg_start = ""
    arg_end = ""
    if conf.start != "":
        arg_start = f"-ss {conf.start}"
    if conf.end != "":
        arg_end = f"-to {conf.end}"

    if conf.twopass:
        print("> encoding... (1st pass)")
        os.system(
            f"nice -n {conf.nice} ffmpeg -i {conf.f_in} -loglevel error -stats {arg_crop} -threads {arg_threads} -c:v libvpx-vp9 -b:v {avgrate[p]} -minrate {minrate[p]} -maxrate {maxrate[p]} -tile-columns {arg_tile_columns} -row-mt {arg_row_mt} -g {g[p]} -quality {quality[p]} -speed {first_pass_speed[p]} -crf {crf[p]} {arg_start} {arg_end} -an -pass 1 {conf.f_out}")

        print("> encoding... (2nd pass)")
        os.system(
            f"nice -n {conf.nice} ffmpeg -i {conf.f_in} -loglevel error -stats {arg_crop} -threads {arg_threads} -c:v libvpx-vp9 -b:v {avgrate[p]} -minrate {minrate[p]} -maxrate {maxrate[p]} -tile-columns {arg_tile_columns} -row-mt {arg_row_mt} -g {g[p]} -quality {quality[p]} -speed {second_pass_speed[p]} -crf {crf[p]} {arg_start} {arg_end} -c:a libopus -b:a {audiorate[p]} {arg_complex_filter} -sn -pass 2 -y {conf.f_out}")
    else:
        print("> encoding...")
        os.system(
            f"nice -n {conf.nice} ffmpeg -i {conf.f_in} -loglevel error -stats {arg_crop} -threads {arg_threads} -c:v libvpx-vp9 -b:v {avgrate[p]} -minrate {minrate[p]} -maxrate {maxrate[p]} -tile-columns {arg_tile_columns} -row-mt {arg_row_mt} -g {g[p]} -quality {quality[p]} -speed {second_pass_speed[p]} -crf {crf[p]} {arg_start} {arg_end} -c:a libopus -b:a {audiorate[p]} {arg_complex_filter} -sn {conf.f_out}")
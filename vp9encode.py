#!/usr/bin/env python3
import getopt
import json
import os
import subprocess
import sys

#  @formatter:off   libvpx-vp9 encoder parameters (@ 24,25,30 fps)
# profile                  0        1        2        3
p_width =             [    3860,    2560,    1920,    1280]
p_height =            [    2160,    1440,    1080,     720]
p_avgrate =           ["12000k", "6000k", "1800k", "1024k"]
p_minrate =           [ "6000k", "3000k",  "900k",  "512k"]
p_maxrate =           ["17400k", "8700k", "2610k", "1485k"]
p_crf =               [      15,      24,       31,     32]
p_quality =           [  "good",  "good",   "good", "good"]
p_tile_columns =      [       3,       3,        2,      2]
p_g =                 [     240,     240,      240,    240]
p_first_pass_speed =  [       4,       4,        4,      4]
p_second_pass_speed = [       2,       2,        2,      2]
# @formatter:on


def print_usage(code):
    print("vp9encode usage:\n\n"
          "parameters:\n"
          "-i, --in\t  : input file (required)\n"
          "-o, --out\t  : output file (.webm, optional)\n"
          "-l, --lang\t  : languages to include (eng,deu..., optional)\n"
          "-s, --start\t  : start (00:00:00, optional)\n"
          "-e, --end\t  : end (00:00:00, optional)\n"
          "-n, --nice\t  : niceness (19=low priority, -20=high priority, optional)\n\n"
          "flags:\n"
          "-c, --crop\t  : autocrop black borders\n"
          "-m, --multithread : enable multithreading\n"
          "-t, --twopass\t  : use two-pass encoding\n")
    exit(code)


class Config:
    def __init__(self, f_in, f_out, start, end, lang, nice, crop, multithread, twopass):
        self.f_in = f_in
        if f_out == "":
            self.f_out = os.path.splitext(f_in)[0] + ".webm"
        else:
            self.f_out = f_out
        self.start = start
        self.end = end
        self.lang = lang
        self.nice = nice
        self.crop = crop
        self.multithread = multithread
        self.twopass = twopass


class Metadata:
    def __init__(self, codec, width, height, audio_streams):
        self.codec = codec
        self.width = int(width)
        self.height = int(height)
        self.audio_streams = audio_streams


def load_config(argv):
    f_in = ""
    f_out = ""
    start = ""
    end = ""
    lang = []
    nice = 19
    crop = False
    multithread = False
    twopass = False
    if not 1 <= len(argv):
        print_usage(1)

    try:
        opts, args = getopt.getopt(argv, "i:o:l:s:e:n:cmt",
                                   ["in=", "out=", "lang=", "start=", "end=", "nice=", "crop", "multithread",
                                    "twopass"])
    except getopt.GetoptError:
        print_usage(1)
    for opt, arg in opts:
        if opt in ("-i", "--in"):
            f_in = str(arg)
        elif opt in ("-o", "--out"):
            f_out = str(arg)
        elif opt in ("-l", "--lang"):
            lang = arg.lower().split(",")
        elif opt in ("-s", "--start"):
            start = str(arg)
        elif opt in ("-e", "--end"):
            end = str(arg)
        elif opt in ("-n", "--nice"):
            nice = int(arg)
        elif opt in ("-c", "--crop"):
            crop = True
        elif opt in ("-m", "--multithread"):
            multithread = True
        elif opt in ("-t", "--twopass"):
            twopass = True
    if f_in == "":
        print_usage(1)
    if f_out == "":
        f_out = os.path.splitext(f_in)[0] + ".webm"
    return Config(f_in, f_out, start, end, lang, nice, crop, multithread, twopass)


def load_metadata(f_in):
    with os.popen(f"ffprobe -hide_banner -show_streams -print_format json '{f_in}' 2>/dev/null") as meta_json:
        all_streams = json.load(meta_json)
    video_stream = [stream for stream in all_streams["streams"] if stream["codec_type"] == "video"][0]
    return Metadata(audio_streams=[stream for stream in all_streams["streams"] if stream["codec_type"] == "audio"],
                    codec=video_stream["codec_name"], width=int(video_stream["width"]),
                    height=video_stream["height"])


def print_config(config):
    print(f"> config:\n\tin:  {config.f_in}\n\tout: {config.f_out}\n\tautocrop: {config.crop}")


def print_metadata(meta):
    print(f"> metadata:\n\tres: {meta.width}x{meta.height}\n\tcodec: {meta.codec}")
    print("\taudio streams:\n\t\t[index] language : sample_fmt : sample_rate : layout")
    for s in meta.audio_streams:
        print("\t\t[%d] %s : %s : %s : %s" % (
            s['index'], s['tags'].get('language'), s['sample_fmt'], s['sample_rate'], s['channel_layout']
        ))


def determine_profile_index(width, height):
    p = -1
    d = 1_000_000
    for i in range(len(p_height)):
        t = ((p_width[i] - width) ** 2 + (p_height[i] - height) ** 2) ** 0.5
        if t <= d:
            p = i
            d = t
    return p


def filter_audio_streams(audio_streams, lang):
    if len(lang) == 0 or len(audio_streams) == 1:
        return audio_streams
    filtered = [s for s in audio_streams if s["tags"].get("language") in lang]
    if len(filtered) > 0:
        return filtered
    else:
        return audio_streams


def generate_ffmpeg_complex_audio_filter(audio_streams):
    fix_libopus_cl = {"5.0(side)": "5.0", "5.1(side)": "5.1"}  # fix libopus inability to encode (side)-channels
    maps = ["[:%d]channelmap=channel_layout='%s'" % (s["index"], fix_libopus_cl[s["channel_layout"]])
            if s.get("channel_layout") in fix_libopus_cl.keys() else "[:%d]anull" % (s["index"])
            for s in audio_streams]
    return ["-filter_complex", ";".join(maps)]


def generate_ffmpeg_audio_metadata(audio_streams):
    metadata = []
    for i, s in enumerate(audio_streams):
        lang = str(s['tags'].get('language'))
        layout = str(s.get('channel_layout') or '').upper()
        metadata += [f"-metadata:s:a:{i}",
                     f"language=\"{lang}\"",
                     f"-metadata:s:a:{i}",
                     f"title=\"{s['tags'].get('title') or lang.upper() + ' ' + layout}\""]
    return metadata


def compute_crop(nice, f_in):
    crop = os.popen(
        f"nice -n {nice} ffmpeg -ss 600 -i {f_in}" +
        " -t 120 -vsync vfr -vf cropdetect -f null - 2>&1 | awk '/crop/ { print $NF }' | tail -1") \
        .readline().removesuffix("\n")
    return crop


def encode(conf):
    print(f"> loading metadata...")
    meta = load_metadata(conf.f_in)
    print_metadata(meta)

    p = determine_profile_index(width=meta.width, height=meta.height)
    print(f"> using profile {p} ({p_height[p]}p)")

    a = filter_audio_streams(audio_streams=meta.audio_streams, lang=conf.lang)
    print(f"> including audio streams: " + ",".join([str(stream["index"]) for stream in a]))
    arg_complex_filter = generate_ffmpeg_complex_audio_filter(a)

    arg_crop = []
    if conf.crop:
        print("> running cropdetect...")
        crop = compute_crop(nice=conf.nice, f_in=conf.f_in)
        print(f"\t{crop}")
        arg_crop = ["-vf", crop]

    arg_multithread = ["-threads", "1"]
    if conf.multithread:
        arg_multithread = ["-threads", str(p_tile_columns[p] * 4), "-tile-columns",
                           str(p_tile_columns[p]), "-row-mt", "1"]
    print(f"> using {arg_multithread[1]} thread(s)")

    arg_time = []
    if conf.start != "":
        arg_time += ["-ss", conf.start]
    if conf.end != "":
        arg_time += ["-to", conf.end]

    arg_complex_filter = generate_ffmpeg_complex_audio_filter(meta.audio_streams)
    arg_audio_metadata = generate_ffmpeg_audio_metadata(meta.audio_streams)

    base_cmd = ["nice", "-n", str(conf.nice), "ffmpeg", "-i", conf.f_in, "-loglevel", "error", "-stats",
                "-c:v", "libvpx-vp9", "-b:v", p_avgrate[p], "-minrate", p_minrate[p], "-maxrate", p_maxrate[p],
                "-g", str(p_g[p]), "-quality", p_quality[p], "-crf", str(p_crf[p])]
    base_cmd += arg_crop + arg_multithread + arg_time

    if conf.twopass:
        print("> encoding... (1st pass)")
        subprocess.run(base_cmd + ["-speed", str(p_first_pass_speed[p]), "-an", "-sn", "-pass", "1", conf.f_out])
        print("> encoding... (2nd pass)")
        subprocess.run(base_cmd + ["-speed", str(p_second_pass_speed[p]), "-c:a", "libopus"]
                       + arg_complex_filter + arg_audio_metadata + ["-sn", "-pass", "2", "-y", conf.f_out])
    else:
        print("> encoding...")
        subprocess.run(base_cmd + ["-speed", str(p_second_pass_speed[p]), "-c:a", "libopus"]
                       + arg_complex_filter + arg_audio_metadata + ["-sn", conf.f_out])


def main(argv):
    conf = load_config(argv[1:])
    print_config(conf)
    encode(conf)


if __name__ == "__main__":
    main(sys.argv)

import json
import os

# libvpx-vp9 encoder params
avgrate = "1800k"
minrate = "900k"
maxrate = "2800k"
tile_columns = 2
g = 240
quality = "good"
crf = 31
speed = 4

if __name__ == '__main__':
    print("Universal 1080p 24/25/30fps vp9 encoding guide")
    print("Video file:")
    file = input()

    all_streams = json.load(os.popen(f"ffprobe -hide_banner -show_streams -print_format json {file} 2>null"))
    audio_streams = [stream for stream in all_streams["streams"] if stream["codec_type"] == "audio"]
    print("Choose audio streams: (comma separated, optional)")
    print("[index] language : channels : sample_fmt : sample_rate : hearing_impaired? : visual_impaired?")
    for stream in audio_streams:
        print(
            f"[{stream['index']}] {stream['tags']['language']} : {stream['tags']['title']} : {stream['sample_fmt']} : {stream['sample_rate']} : {stream['disposition']['hearing_impaired']} : {stream['disposition']['visual_impaired']}")
    wanted_streams = input().split(",")
    if len(wanted_streams) > 0:
        selected_streams = [stream for stream in audio_streams if str(stream["index"]) in wanted_streams]
        fix_libopus_cl = {"5.0(side)": "5.0", "5.1(side)": "5.1"}  # fix libopus inability to encode (side)-channels
        maps = ["[:%d]channelmap=channel_layout='%s'" % (stream["index"], fix_libopus_cl[stream["channel_layout"]])
                if stream.get("channel_layout") in fix_libopus_cl.keys() else
                "[:%d]anull" % (stream["index"])
                for stream in selected_streams]
        complex_filter = ";".join(maps)
        if complex_filter != "":
            complex_filter = f"-filter_complex \"{complex_filter}\""
    del all_streams, audio_streams, wanted_streams, selected_streams, fix_libopus_cl, maps

    print("Start (00:00:00): (optional)")
    start = input()
    if start != "":
        start = f"-ss {start}"

    print("End (00:00:00): (optional)")
    end = input()
    if end != "":
        end = f"-to {end}"

    print("Crop detection timestamp:")
    crop = os.popen(
        f"ffmpeg -ss {input()} -i {file}" + " -t 1 -vsync vfr -vf cropdetect -f null - 2>&1 | awk '/crop/ { "
                                            "print $NF }' | tail -1").readline().removesuffix("\n")

    print("Output file: (optional)")
    out = input()
    if out == "":
        out = os.path.splitext(file)[0] + ".webm\""

    print("Threads:")
    threads = input()

    print("Niceness (19=low priority, -20=high priority):")
    nice = input()

    print("Encoding... (1st pass)")
    os.system(f"nice -n {nice} ffmpeg -i {file} -loglevel error -stats -vf {crop} -threads {threads} -c:v libvpx-vp9 -b:v {avgrate} -minrate {minrate} -maxrate {maxrate} -tile-columns {tile_columns} -g {g} -quality {quality} -crf {crf} {start} {end} -an -pass 1 -speed {speed} -f null -")

    print("Encoding... (2nd pass)")
    os.system(f"nice -n {nice} ffmpeg -i {file} -loglevel error -stats -vf {crop} -threads {threads} -c:v libvpx-vp9 -b:v {avgrate} -minrate {minrate} -maxrate {maxrate} -tile-columns {tile_columns} -g {g} -quality {quality} -crf {crf} {start} {end} -c:a libopus {complex_filter} -sn -pass 2 -speed {speed} -y {out}")

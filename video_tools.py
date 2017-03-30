#!/usr/bin/python

# This toolbox contains tools about the video process

import json
import os
import log_tools


def get_video_resolution(video_file):
    """
    This function use ffprobe which in ffmpeg package
    to get the resolution of the video
    The input is the video file, and the output is the [width, height]
    """
    cmd_line = 'ffprobe -v quiet -print_format json -show_format -show_streams'
    cmd_line = cmd_line + ' ' + video_file

    rst = os.popen(cmd_line).read()
    rst = json.loads(rst)
    streams = rst['streams']
    for stream in streams:
        if 'coded_width' in stream and 'coded_height' in stream:
            width = stream['coded_width']
            height = stream['coded_height']
            return [width, height]
    log_tools.log_err('Can not get the resolution of %s' % video_file)
    return [None, None]

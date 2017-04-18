#!/usr/bin/python

# This toolbox contains tools about the video process

import json
import os
import time_tools
import log_tools


def get_video_info(video_file):
    """
    Get the video infor structure from the ffprobe command
    """
    # Check if file exist
    if not os.path.isfile(video_file):
        log_tools.log_err('Cannot find %s' % video_file)
        return None
    cmd_line = 'ffprobe -v quiet -print_format json -show_format -show_streams'
    cmd_line = cmd_line + ' ' + video_file

    rst = os.popen(cmd_line).read()
    rst = json.loads(rst)
    return rst


def get_video_resolution(video_file):
    """
    This function use ffprobe which in ffmpeg package
    to get the resolution of the video
    The input is the video file, and the output is the [width, height]
    """
    rst = get_video_info(video_file)
    streams = rst['streams']
    for stream in streams:
        if 'coded_width' in stream and 'coded_height' in stream:
            width = stream['coded_width']
            height = stream['coded_height']
            return [width, height]
    log_tools.log_err('Can not get the resolution of %s' % video_file)
    return [None, None]


def get_video_basic_info(video_file):
    """
    Get the video basic information from the detailed info from
    the ffprobe
    The structure is
    info['video'][0/1/2]['title'/'height'/'width'/'bit_rate']
    info['audio'][0/1/2]['title'/'bit_rate'/'channels']
    info['subtitle'][0/1/2]['title'/'codec_name'/'duration']
    info['attachment'][0/1/2]['filename'/'mimetype']
    """
    rst = get_video_info(video_file)
    info = {}
    streams = rst['streams']
    info['video'] = []
    info['audio'] = []
    info['subtitle'] = []
    info['attachment'] = []
    for stream in streams:
        if stream['codec_type'] == 'video':
            st = {}
            st['height'] = stream['coded_height']
            st['width'] = stream['coded_width']
            try:
                st['bit_rate'] = stream['bit_rate']
            except:
                st['bit_rate'] = 'n/a'
            try:
                st['title'] = stream['tags']['title']
            except:
                st['title'] = 'n/a'
            info['video'].append(st)
            continue
        if stream['codec_type'] == 'audio':
            st = {}
            try:
                st['bit_rate'] = stream['bit_rate']
            except:
                st['bit_rate'] = 'n/a'
            try:
                st['title'] = stream['tags']['title']
            except:
                st['title'] = 'n/a'
            try:
                st['channels'] = stream['channels']
            except:
                st['channels'] = 'n/a'

            info['audio'].append(st)
            continue
        if stream['codec_type'] == 'subtitle':
            st = {}
            try:
                st['title'] = stream['tags']['title']
            except:
                st['title'] = 'n/a'
            try:
                st['codec_name'] = stream['codec_name']
            except:
                st['codec_name'] = 'n/a'
            try:
                st['duration'] = stream['duration']
            except:
                st['duration'] = 'n/a'
            info['subtitle'].append(st)
            continue
        if stream['codec_type'] == 'attachment':
            st = {}
            try:
                st['filename'] = stream['tags']['filename']
            except:
                st['filename'] = 'n/a'
            try:
                st['mimetype'] = stream['tags']['mimetype']
            except:
                st['mimetype'] = 'n/a'
            info['attachment'].append(st)
            continue

    return info


def print_video_basic_info(video_file):
    """
    Print the basic information of the video
    and return the basic info
    """
    info = get_video_basic_info(video_file)
    for idx, video in enumerate(info['video']):
        log_tools.log_info('[video stream %d] \033[01;32m%dx%d\033[0m, \
title: \033[01;32m%s\033[0m, bit_rate: \033[01;32m%s\033[0m'
                           % (idx,
                              video['width'],
                              video['height'],
                              video['title'],
                              str(video['bit_rate'])))

    for idx, audio in enumerate(info['audio']):
        log_tools.log_info('[audio stream %d] title: \033[01;32m%s\033[0m, \
channels: \033[01;32m%d\033[0m, bit_rate: \033[01;32m%s\033[0m'
                           % (idx, audio['title'],
                              audio['channels'], audio['bit_rate']))

    for idx, sub in enumerate(info['subtitle']):
        log_tools.log_info('[subtitle stream %d] title: \033[01;32m%s\033[0m, \
codec_name: \033[01;32m%s\033[0m, duration: \033[01;32m%s\033[0m'
                           % (idx, sub['title'],
                              sub['codec_name'], sub['duration']))

    for idx, att in enumerate(info['attachment']):
        log_tools.log_info('[attachment stream %d] filename: \033[01;32m%s\033[0m, \
mimetype: \033[01;32m%s\033[0m' % (idx, att['filename'], att['mimetype']))
    return info


def get_video_length(video_file):
    """
    Get the video length in seconds
    If can not, return None
    """
    info = get_video_info(video_file)
    try:
        sec = info['format']['duration']
    except:
        return None
    return float(sec)


def get_video_length_str(video_file):
    """
    Get the video length in readable string
    if not, return None
    """
    sec = get_video_length(video_file)
    if sec is not None:
        return time_tools.sec2time(sec)
    else:
        return None

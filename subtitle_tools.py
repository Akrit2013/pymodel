#!/usr/bin/python
# -*- coding:utf-8-*-

# This tools contains functions used for video subtitle

import txt_tools
import easyprogressbar as eb
import char_tools
import log_tools


def count_chi_in_line(line):
    """
    Count the chinese char in given line
    Return the [chinese counter, total non-number counter]
    """
    # Check and convert the encoding to unicode
    line = char_tools.str2unicode(line)
    chi_counter = 0
    total_counter = 0
    try:
        for ch in line:
            if ch >= u"\u4e00" and ch <= u"\u9fa6":
                # Chinese char
                chi_counter += 1
            elif ch >= u'\u0030' and ch <= u'\u0039':
                # Number Char
                continue
            total_counter += 1
    except:
        return [0, 0]
    return [chi_counter, total_counter]


def detect_language(subtitle):
    """
    This function detect the language of a subtitle file
    and return the a string indicating the language in mkvmerge format
    Use mkvmerge --list-languages to show the support language code
    current, only support
    Chinese     chi
    English     eng
    """
    # Load the subtitle
    lines = txt_tools.read_lines_from_txtfile(subtitle)
    # The total char counter
    char_counter = 0
    # The chinese charactor counter
    chi_counter = 0
    # Check the lines
    bar = eb.EasyProgressBar()
    bar.set_end(len(lines))
    bar.start()

    # The counter of bad line, which returns [0, 0]
    badlines = 0
    totallines = len(lines)

    log_tools.log_info('Checking the language of %s' % subtitle)
    for line in lines:
        [chi, total] = count_chi_in_line(line)
        chi_counter += chi
        char_counter += total
        bar.update_once()
        if chi == 0 and total == 0:
            badlines += 1

    bar.finish()
    rate = float(chi_counter) / float(char_counter)
    line_rate = float(badlines) / float(totallines)

    if line_rate > 0.1:
        log_tools.log_warn('Can not determine the language type of %s'
                           % subtitle)
        return None

    if rate > 0.05:
        lang = 'chi'
    else:
        lang = 'eng'
    log_tools.log_info('Detected language: \033[01;31m%s\033[0m: %f, \
badline: %f' % (lang, rate, line_rate))
    return lang


def guess_language(subtitle):
    """
    This function guess the language according to the file name
    such as
    xxx.chi.srt
    xxx.eng&cht.srt
    xxx.简体.srt

    If the language can not be gussed, return None
    """
    # Try to decode if Chinese char exist
    word_list = subtitle.split('.')
    cand_list = []
    if len(word_list) <= 2:
        return None
    if len(word_list) == 3:
        cand_string = word_list[-2]
        cand_list.append(word_list[-2].lower())
    else:
        cand_string = word_list[-2] + word_list[-3]
        cand_list.append(word_list[-2].lower())
        cand_list.append(word_list[-3].lower())

    cand_string = cand_string.lower()
    # Parse the candidate string
    if 'chs' in cand_string:
        return 'chi'
    if 'chn' in cand_string:
        return 'chi'
    if 'chinese' in cand_string:
        return 'chi'
    if 'cht' in cand_string:
        return 'chi'
    if 'chi' in cand_string:
        return 'chi'
    if '简体' in cand_string:
        return 'chi'
    if '繁体' in cand_string:
        return 'chi'
    if '中文' in cand_string:
        return 'chi'
    if 'eng' in cand_string:
        return 'eng'
    if '英文' in cand_string:
        return 'eng'
    if 'english' in cand_string:
        return 'eng'
    if 'cn' in cand_list:
        return 'chi'
    if 'hk' in cand_list:
        return 'chi'
    if 'tw' in cand_list:
        return 'chi'
    if 'en' in cand_list:
        return 'eng'

    return None


def guess_track_name(subtitle):
    """
    This function guess the subtitle name according to the subtitle
    file name
    """
    # Try to decode if Chinese char exist
    word_list = subtitle.split('.')
    cand_list = []
    if len(word_list) <= 2:
        return None
    if len(word_list) == 3:
        cand_string = word_list[-2]
        cand_list.append(word_list[-2].lower())
    else:
        cand_string = word_list[-2] + word_list[-3]
        cand_list.append(word_list[-2].lower())
        cand_list.append(word_list[-3].lower())

    cand_string = cand_string.lower()
    has_chi = False
    has_eng = False
    has_cht = False
    # Parse the candidate string
    if 'cn' in cand_list:
        has_chi = True
    if 'hk' in cand_list:
        has_cht = True
    if 'tw' in cand_list:
        has_cht = True
    if 'en' in cand_list:
        has_eng = True

    if 'chs' in cand_string:
        has_chi = True
    if 'chn' in cand_string:
        has_chi = True
    if 'cht' in cand_string:
        has_cht = True
    if 'chi' in cand_string:
        has_chi = True
    if '简体' in cand_string:
        has_chi = True
    if '繁体' in cand_string:
        has_cht = True
    if '中文' in cand_string:
        has_chi = True
    if 'chinese' in cand_string:
        has_chi = True
    if 'eng' in cand_string:
        has_eng = True
    if '英文' in cand_string:
        has_eng = True
    if 'english' in cand_string:
        has_eng = True

    if has_eng and has_chi:
        return '中英双语'
    if has_cht and has_eng:
        return '繁体中英'
    if has_eng:
        return '英文'
    if has_chi:
        return '中文'
    if has_cht:
        return '繁体中文'

    return None

#!/usr/bin/env python

import curses
import argparse
import time
import signal
import socket
import os
import string
from functools import partial

def _tail_gen(fin):
    while True:
        line = fin.readline()
        if line:
            yield line+'\r'
        else:
            _tail(fin)

def _tail(fin):
    while True:
        where = fin.tell()
        line = fin.readline()
        if not line:
            time.sleep(1)
            fin.seek(where)
        else:
            yield line

def _shift_screen(screen, height):
    screen.scrollok(True)
    screen.setscrreg(1, height - 1)
    screen.scroll()

def _end(screen):
    screen.clear()
    screen.refresh()
    curses.endwin()
    return 0

def _print_title(screen, file_name, width, hostname):
    screen.clear()
    if hostname:
        file_name = '{0} @ {1} '.format(file_name , socket.gethostname())
    screen.addnstr(0, 0, file_name, width - 1, (curses.A_UNDERLINE|curses.A_BOLD))
    screen.refresh()

def _wrap_text(screen, current, height, width, line, wrap_indicator):
    start = width
    while(start < len(line)):
        next_segment = line[start:start + width]
        if current > height -2:
            _shift_screen(screen, height)
            current = height - 2
        l = '{0}{1}'.format(wrap_indicator, next_segment)
        length = start + width - len(wrap_indicator)
        screen.addnstr(current, 0, l, length)
        start += width - len(wrap_indicator)
        current += 1

    screen.refresh()
    return current

def _display_file(fin, screen, height, width, wrap_arround=True, wrap_indicator=''):

    # Read through file to get to end of file for tail
    lines = fin.readlines()
    # Adjust to only display lines equal to height of screen
    if len(lines) > height - 2:
        lines = lines[-(height-2):]

    # add last lines to screen
    current = 1
    for l in range(len(lines)):
        screen.addnstr(current, 0, lines[l], width)
        current += 1
        if wrap_arround:
            current = _wrap_text(screen, current, height, width, lines[l], wrap_indicator)
        if current > height - 2:
            _shift_screen(screen, height)
            current = height - 2

    # start tail
    screen.refresh()
    for l in _tail_gen(fin):
        if current > height - 2:
            _shift_screen(screen, height)
            current = height - 2
        screen.addnstr(current, 0, l, width)
        current += 1
        if wrap_arround:
            current = _wrap_text(screen, current, height, width, l, wrap_indicator)
        screen.refresh()

def handle_intrupt(screen, signum, stack):
    exit(_end(screen))

def main(args):

    rc_configuration = {
            'wrap_indicator':''
            }

    rcfile = os.path.expanduser(args.rc_file)
    if os.path.isfile(rcfile):
        with open(rcfile) as rc:
            for l in rc:
                l = string.strip(l)
                split = l.split('=')
                if split[0] in rc_configuration:
                    rc_configuration[split[0]] = split[1]

    screen = curses.initscr()

    signal.signal(signal.SIGINT, partial(handle_intrupt, screen))

    height, width = screen.getmaxyx()

    _print_title(screen, args.file, width, args.name)

    fin = open(args.file, 'r')

    wrap_indicator = rc_configuration['wrap_indicator']
    _display_file(fin, screen, height, width, args.no_wrap, wrap_indicator)

    _end(screen)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('file', help='file to tail')
    parser.add_argument('-n', '--name', help='display host name of computer with title', default=False, action='store_true')
    parser.add_argument('-w', '--no_wrap', help='wrap text for lines longer than width of the screen', default=True, action='store_false')
    parser.add_argument('-c', '--rc_file', help='path to rc file [default is ~/.ntabrc]', default='~/.ntabrc')

    return parser.parse_args()

if __name__ == '__main__':
    main(parse_args())

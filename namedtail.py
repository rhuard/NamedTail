#!/usr/bin/env python

import curses
import argparse
import time
import signal
import socket
import os
import string
from functools import partial

# used to check against user input
yes = ['yes', 'Yes', 'YES', 'y', 'Y']
no = ['no', 'No', 'NO', 'n', 'N']

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

def _search_addnstr(screen, current, current_y, line, length, search, attributes=0):
    colored = False
    for s in search:
        if s in line:
            colored = True
            screen.addnstr(current, current_y, line, length, attributes)
            break
    if colored is False:
        screen.addnstr(current, current_y, line, length)

def _wrap_text(screen, current, height, width, line, wrap_indicator, search, attributes=0):
    start = width
    while(start < len(line)):
        next_segment = line[start:start + width]
        if current > height -2:
            _shift_screen(screen, height)
            current = height - 2
        l = '{0}{1}'.format(wrap_indicator, next_segment)
        length = start + width - len(wrap_indicator)
        _search_addnstr(screen, current, 0, l, length, search, attributes)
        # screen.addnstr(current, 0, l, length)
        start += width - len(wrap_indicator)
        current += 1

    screen.refresh()
    return current

def _display_file(fin, screen, height, width, search, wrap_arround=True, wrap_indicator='', attributes=0):

    # Read through file to get to end of file for tail
    lines = fin.readlines()
    # Adjust to only display lines equal to height of screen
    if len(lines) > height - 2:
        lines = lines[-(height-2):]

    # add last lines to screen
    current = 1
    for l in range(len(lines)):
        _search_addnstr(screen, current, 0, lines[l], width, search, attributes)
        # screen.addnstr(current, 0, lines[l], width)
        current += 1
        if wrap_arround:
            current = _wrap_text(screen, current, height, width, lines[l], wrap_indicator, search, attributes=0)
        if current > height - 2:
            _shift_screen(screen, height)
            current = height - 2

    # start tail
    screen.refresh()
    for l in _tail_gen(fin):
        if current > height - 2:
            _shift_screen(screen, height)
            current = height - 2
        _search_addnstr(screen, current, 0, l, width, search, attributes)
        # screen.addnstr(current, 0, l, width)
        current += 1
        if wrap_arround:
            current = _wrap_text(screen, current, height, width, l, wrap_indicator, search, attributes)
        screen.refresh()

def _set_text_attributes(attributes_config):
    attributes = 0

    allowed_attributes= {
                    'bold': curses.A_BOLD,
                    'reverse': curses.A_REVERSE,
                    'underline': curses.A_UNDERLINE,
                        }

    sp = attributes_config.split(':')
    for s in sp:
        if s.lower() in allowed_attributes:
            attributes |= allowed_attributes[s.lower()]
        else:
            print 'WARNING: {0} is not a valid text_attribute'.format(s)
            quit = raw_input('quit [y/N] ')
            if quit in yes:
                exit(0)

    return attributes

def handle_intrupt(screen, signum, stack):
    exit(_end(screen))


def main(args):

    configurations = {
            'wrap_indicator':'',
            'text_attribute':''
            }

    config_file = os.path.expanduser(args.config_file)
    if os.path.isfile(config_file):
        with open(config_file) as config:
            for l in config:
                l = string.strip(l)
                split = l.split('=')
                if split[0] in configurations:
                    value = split[1].replace('"', "'")
                    value = string.strip(value, "'")
                    configurations[split[0]] = value
                else:
                    print 'WARNING: {0} is not a valid config option'.format(split[0])
                    quit = raw_input('quit [y/N] ')
                    if quit in yes:
                        exit(0)


    wrap_indicator = configurations['wrap_indicator']
    attributes = _set_text_attributes(configurations['text_attribute'])

    screen = curses.initscr()

    signal.signal(signal.SIGINT, partial(handle_intrupt, screen))

    height, width = screen.getmaxyx()

    _print_title(screen, args.file, width, args.name)

    fin = open(args.file, 'r')

    _display_file(fin, screen, height, width, args.search, args.no_wrap, wrap_indicator, attributes)

    _end(screen)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('file', help='file to tail')
    parser.add_argument('-n', '--name', help='display host name of computer with title', default=False, action='store_true')
    parser.add_argument('-w', '--no_wrap', help='wrap text for lines longer than width of the screen', default=True, action='store_false')
    parser.add_argument('-c', '--config_file', help='path to config file [default is ~/.ntabconfig', default='~/.ntabconfig')
    parser.add_argument('-s', '--search', help='strings to search for', nargs='*', default=[])

    return parser.parse_args()

if __name__ == '__main__':
    main(parse_args())

#!/usr/bin/env python

import curses
import argparse
import time
import signal
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

def _print_title(screen, file_name, width):
    screen.clear()
    screen.addnstr(0, 0, file_name, width - 1, (curses.A_UNDERLINE|curses.A_BOLD))
    screen.refresh()

def _display_file(fin, screen, height, width):

    # Read through file to get to end of file for tail
    lines = fin.readlines()
    # Adjust to only display lines equal to height of screen
    if len(lines) > height - 2:
        lines = lines[-(height-2):]

    # add last lines to screen
    for l in range(len(lines)):
        screen.addnstr(l+1, 0, lines[l], width - 1)

    screen.refresh()
    current = len(lines) + 1
    for l in _tail_gen(fin):
        if current > height - 2:
            _shift_screen(screen, height)
            current = height - 2
        screen.addnstr(current, 0, l, width - 1)
        screen.refresh()
        current += 1

def handle_intrupt(screen, signum, stack):
    exit(_end(screen))

def main(args):
    screen = curses.initscr()

    signal.signal(signal.SIGINT, partial(handle_intrupt, screen))

    height, width = screen.getmaxyx()

    _print_title(screen, args.file, width)

    fin = open(args.file, 'r')

    _display_file(fin, screen, height, width)

    _end(screen)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('file', help='file to tail')

    return parser.parse_args()

if __name__ == '__main__':
    main(parse_args())

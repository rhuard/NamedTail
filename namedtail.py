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

def _shift_screen(screen, height):
    screen.scrollok(True)
    screen.setscrreg(1, height - 1)
    screen.scroll()

def _end(screen):
    screen.clear()
    screen.refresh()
    curses.endwin()
    return 0

def _print_title(screen, file_name):
    screen.clear()
    screen.addstr(0,0, file_name, (curses.A_UNDERLINE|curses.A_BOLD))
    screen.refresh()

def _tail(fin):
    while True:
        where = fin.tell()
        line = fin.readline()
        if not line:
            time.sleep(1)
            fin.seek(where)
        else:
            yield line

def _display_file(fin, screen, height):
    current = 1
    for l in _tail_gen(fin):
        screen.addstr(current,0, l)
        screen.refresh()
        current += 1
        if current > height - 2:
            _shift_screen(screen, height)
            current = height - 2

def handle_intrupt(screen, signum, stack):
    exit(_end(screen))

def main(args):
    screen = curses.initscr()

    signal.signal(signal.SIGINT, partial(handle_intrupt, screen))

    height, width = screen.getmaxyx()

    _print_title(screen, args.file)

    fin = open(args.file, 'r')

    _display_file(fin, screen, height)

    _end(screen)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('file', help='file to tail')

    return parser.parse_args()


if __name__ == '__main__':
    main(parse_args())

#!/usr/bin/env python
import curses

from sys import stdin, stdout
import select


class raw_terminal(object):
    """ change terminal mode that the input is unbuffered """
    def __init__(self, fd):
        self.fd = fd

    def __enter__(self):
        curses.initscr()

        if not any(curses.termname().startswith(t) for t in (b'xterm', b'screen')):
            raise Exception(f"This backend only supports xterm as terminal emulator. Got: '{curses.termname()}'.")

        curses.cbreak()

    def __exit__(self, type, value, traceback):
        curses.endwin()


def read_until(fd, delim):
    out = ""
    c = stdin.read(1)
    while c != delim:
        out += c
        c = stdin.read(1)
    return out


def xterm_pixels(fallback=(480, 320)):
    """ Get the width and heigth in pixels of the xterm window """
    code = "\x1b\x5b\x31\x34\x74\x0a"

    with raw_terminal(stdin):
        stdout.write(code)
        stdout.flush()

        if select.select([stdin,], [], [], 0.1)[0]:
            c = stdin.read(1)
            assert c == '\x1b'
            read_until(stdin, ';')
            height = read_until(stdin, ';')
            width = read_until(stdin, 't')
        else:
            return fallback

    return (int(width), int(height))

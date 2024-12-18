################################################################################
# a4.log --- minimal logging with timestamp and automatic coloring
################################################################################
__all__ = ['level', 'dbg', 'info', 'note', 'warn', 'err']

import os
import sys
import datetime as dt

ERROR = 1
WARN  = 2
NOTE  = 3
INFO  = 4
DEBUG = 5
fork  = False

_level = INFO if os.environ.get('DBG', '0') == '0' else DEBUG
_pipe = not sys.stdout.isatty()

def _color(color: int = 0):
    if not fork and _pipe:
        return ''
    return f'\033[1;{color}m' if color else '\033[0m'


def _ts():
    return str(dt.datetime.now())[:-3]


def level(level = None):
    global _level

    if level is None:
        return _level

    if isinstance(level, str):
        first = level[0].lower()
        if   first == 'e':
            _level = ERROR
        elif first == 'w':
            _level = WARN
        elif first == 'i':
            _level = INFO
        elif first == 'n':
            _level = NOTE
        elif first == 'd':
            _level = DEBUG
        else:
            _level = 0
    else:
        _level = level

    if _level < ERROR:
        _level = ERROR
    elif _level > DEBUG:
        _level = DEBUG

    return _level


def err(msg):
    if _level >= ERROR:
        print(f'{_color(31)}[{_ts()}] ERR  {msg}{_color()}\n', end='',
              file=sys.stderr if fork else sys.stdout)


def warn(msg):
    if _level >= WARN:
        print(f'{_color(33)}[{_ts()}] WARN {msg}{_color()}\n', end='',
              file=sys.stderr if fork else sys.stdout)


def note(msg):
    if _level >= NOTE:
        print(f'{_color(32)}[{_ts()}] NOTE {msg}{_color()}\n', end='',
              file=sys.stderr if fork else sys.stdout)


def info(msg):
    if _level >= INFO:
        print(            f'[{_ts()}] INFO {msg}{_color()}\n', end='',
              file=sys.stderr if fork else sys.stdout)


def dbg(msg):
    if _level >= DEBUG:
        print(f'{_color(37)}[{_ts()}] DBG  {msg}{_color()}\n', end='',
              file=sys.stderr if fork else sys.stdout)

### a4/log.py ends here

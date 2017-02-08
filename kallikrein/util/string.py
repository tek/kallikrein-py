from amino import __

from hues import huestr


def green(msg: str) -> str:
    return huestr(msg).green.colorized


def red(msg: str) -> str:
    return huestr(msg).red.colorized


def yellow(msg: str) -> str:
    return huestr(msg).yellow.colorized

indent = __.map(' {}'.format)

green_check = green('✓')

red_cross = red('✗')

yellow_clock = yellow('⌚')

__all__ = ('indent', 'green_check', 'red_cross', 'green', 'red',
           'yellow_clock')

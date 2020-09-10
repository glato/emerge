"""
Contains shared/common methods and functions.
"""

# Authors: Grzegorz Lato <grzegorz.lato@gmail.com>
# License: MIT

from typing import List
from string import Template


class DeltaTemplate(Template):
    delimiter = "%"


def camel_case_to_words(camel_case: str) -> str:
    """
    Returns:
        str: A nice string of words from a camel case string.
    """
    pretty: List = []
    for char in camel_case:
        if char.isupper():
            pretty.append(' ')
            pretty.append(char.lower())
        else:
            pretty.append(char)
    return ''.join(map(str, pretty[1:]))


def camel_to_kebab_case(camel_case: str) -> str:
    """
    Returns:
        str: A kebab case string from a given camel case string.
    """
    kebab: List = []
    for char in camel_case:
        if char.isupper():
            kebab.append('-')
            kebab.append(char.lower())
        else:
            kebab.append(char)
    return ''.join(map(str, kebab[1:]))


def format_timedelta(timedelta, fmt):
    """Returns a human readable timedelta.
    Inspired from Joe McCarthy
    https://stackoverflow.com/questions/8906926/formatting-timedelta-objects/8907407
    """
    delta_format = {}
    milliseconds = timedelta.microseconds / 1000
    hours, rem = divmod(timedelta.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    delta_format["H"] = '{:02d}'.format(hours)
    delta_format["M"] = '{:02d}'.format(minutes)
    delta_format["S"] = '{:02d}'.format(seconds)
    delta_format["s"] = '{:.0f}'.format(milliseconds)
    template = DeltaTemplate(fmt)
    return template.substitute(**delta_format)

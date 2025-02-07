# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# #-------------------------------------------------------------
# # French
# #-------------------------------------------------------------
#
# def manageSeparator(amount, digits=0, separator=' '):
#     if amount:
#         amount_str = str((amount)).split('.')
#         print(amount_str)
#         nb = 0
#         amount_format = []
#         temp = ''
#         for i in reversed(amount_str[0]):
#             if nb == 3:
#                 amount_format.append(separator)
#                 nb = 0
#             else :
#                 nb+=1
#             amount_format.append(i)
#         amount_format.reverse()
#         if digits != 0:
#             amount_format.append('.')
#             amount_format.append(amount_str[1])
#         result = ''.join(amount_format)
#         return result
import re

__test__ = {}

re_digits_nondigits = re.compile(r'\d+|\D+')

__test__['re_digits_nondigits'] = r"""

    >>> re_digits_nondigits.findall('$1234.1234')
    ['$', '1234', '.', '1234']
    >>> re_digits_nondigits.findall('1234')
    ['1234']
    >>> re_digits_nondigits.findall('')
    []

"""


def manageSeparator(format=None, value=None):

    parts = re_digits_nondigits.findall(format % (value,))
    for i in range(len(parts)):
        s = parts[i]
        if s.isdigit():
            parts[i] = _commafy(s)
            break
    return ''.join(parts)


def _commafy(s):
    r = []
    for i, c in enumerate(reversed(s)):
        if i and (not (i % 3)):
            r.insert(0, ' ')
        r.insert(0, c)
    return ''.join(r)
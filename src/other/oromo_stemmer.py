#!/usr/bin/env python
"""
Quick & Dirty Stemmer for Oromo Language
Author = Thamme Gowda
Date = August 16, 2017
Version 0.1
"""

import sys
import re
from argparse import ArgumentParser


tg_pttrn = r'(\w{3})(eessuu|eessaa|eessa|ummaa|nnoo|mmaa|tti|ssa|aan|iin|suu|ama|cha|uuf|uun|nni|oo|ee|uu|ii|aa)(\s|$)'
ulf_pttrn1 = r'(\w{3})(oota|otii|tiin|onni|icha|tichi|chi|ttin|tti|era|jira|tokko|tiif)(\s|$)'
ulf_pttrn2 = r'(\w{3})(oota|ootan|ootaa|ootaan|ota|ttin|otii|onnii|onni|wwan|chi|ichi|tichi|ttin|tti' \
            r'|era|eera|jira|iiru|etti|n|ne|f|fe|tiin|cha|chaaf|ummaa|aatii|tiif)(\s|$)'
split_pttrn = r'\1 -\2\3'
trim_pttrn = r'\1\3'

patterns = {'tg': tg_pttrn,
            'ulf1': ulf_pttrn1,
            'ulf2': ulf_pttrn2}


def oromo_stem_line(line, ptrn=ulf_pttrn2, rplmt=split_pttrn):
    return re.sub(ptrn, rplmt, line)


def oromo_stem(ptrn, rplmt):
    for line in sys.stdin:
        line = oromo_stem_line(line, ptrn, rplmt)
        print(line.strip())


if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('-p', '--pattern', help='Name of pattern: tg, ulf1, ulf2', default='ulf2')
    p.add_argument('-t', '--trim', help='Trim suffixes', action='store_true')
    args = vars(p.parse_args())
    ptrn = patterns[args['pattern']]
    rplmt = trim_pttrn if args['trim'] else split_pttrn
    oromo_stem(ptrn, rplmt)
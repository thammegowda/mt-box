#!/usr/bin/env python3

import re
from argparse import ArgumentParser
from name_scanner import *
import sys


def printerr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


parser = ArgumentParser()
parser.add_argument('-n', help='File having english name tokens.', required=True)
parser.add_argument('-e', help='Source file', required=True)
parser.add_argument('-f', help='Target file', required=True)
parser.add_argument('-strict', help='Strict match Sounds only. reduces false possitives', action='store_true', default=False)
parser.add_argument('-verbose', help='Verbose', action='store_true', default=False)
args = vars(parser.parse_args())
names = read_file(args['n'])

pats = compile_patterns(names, False, True, args['strict'])

es = [line.lower().split() for line in read_file(args['e'])] # english
fs = [line.lower().split() for line in read_file(args['f'])] # foreign
assert len(es) == len(fs)

names = set(names)
verbose = args['verbose']

for k,v in pats.items():
    for ets, fts in zip(es, fs):
        missed = []
        for name in set(ets) & names:
            res = list(lookup(fts, pats[name]))
            if res:
                for r in res:
                    print("%s\t%s" % (name, r))
            else:
                missed.append(name)

        if missed and verbose:
            printerr(">> MISSED %s  :: %s" % (missed, fts))

#!/usr/bin/env python
# coding = utf8
# Author = Thamme Gowda tg@isi.edu
# Date = March 09, 2018

"""
This utility finds ngram overlap between sequences
"""
import sys
from collections import Counter
import math


def count_grams(seq, gram_size):
    return Counter(tuple(seq[i: i + gram_size]) for i in range(len(seq) + 1 - gram_size))


def match(hyp, ref, max_gram=4):

    score = 1.0
    res = []

    for g in range(1, max_gram+1):
        tab1 = count_grams(hyp, g)
        tab2 = count_grams(ref, g)

        n = sum(tab1.values())
        if not res:
            res.append(n)
        common = sum(min(tab1[k], tab2[k]) for k in tab1.keys() & tab2.keys())
        res.append(common)

        if common > 0 and n > 0:
            score *= common / n

    # brevity penalty
    score *= min(1.0, math.exp(1 - (len(ref) / len(hyp))))
    res.insert(0, '%.6f' % score)
    return res


def run(inp, ref, outp, max_gram=4, nocase=False):

    for hyp, ref in zip(inp, ref):
        if nocase:
            hyp = hyp.lower()
            ref = ref.lower()

        hyp, ref = hyp.split(), ref.split()
        res = match(hyp, ref, max_gram)
        outp.write('%s\n' % '\t'.join(map(str, res)))


if __name__ == '__main__':
    assert sys.version_info[0] >= 3
    import argparse
    p = argparse.ArgumentParser(description='Finds ngram overlap between records')
    p.add_argument('-i', '--in', help='Hypothesis input file', default=sys.stdin, type=argparse.FileType('r'))
    p.add_argument('-r', '--ref', help='Reference file', default=sys.stdin, type=argparse.FileType('r'))
    p.add_argument('-o', '--out', help='Output file', default=sys.stdout, type=argparse.FileType('w'))
    p.add_argument('-n', '--max-grams', help='Maximum N Grams match', default=4, type=int)
    p.add_argument('-lc', '--lower-case', help='ignore case', default=False, action='store_true')
    args = vars(p.parse_args())
    run(args['in'], args['ref'], args['out'], args['max_grams'], args['lower_case'])





#!/usr/bin/env python
"""
Useful metrics for evaluating predictions and gold answers
"""
from copy import copy
import logging as log
import numpy as np
from scipy.spatial.distance import cosine

log.basicConfig(level=log.DEBUG)
__author__ = 'Thamme Gowda'
__created__ = 'October 10, 2017'
__version__ = '0.1'


class StrictMatch(object):

    def __call__(self, w1, w2):
        return 1.0 if w1 == w2 else 0.0


class GloveCosine(object):
    """
    Computes cosine similarity between terms using Glove vectors
    """
    def __init__(self, path, limit=None, exp=2):
        log.info("Reading Gloves from %s " % path)
        self.idx2tok, self.gloves = GloveCosine.read_gloves(path, limit)
        self.tok2idx = dict((tok, i) for i, tok in enumerate(self.idx2tok))
        assert len(self.idx2tok) == len(self.tok2idx) == len(self.gloves)
        self.dim = self.gloves.shape[1]
        log.info("Read %d vectors, dimension=%d" % (len(self.gloves), self.dim))
        self.exp = exp

    def glove(self, term):
        if term in self.tok2idx:
            return self.gloves[self.tok2idx[term]]
        return None

    @staticmethod
    def read_gloves(path, limit=None):
        vocab, vectors = [], []
        with open(path) as f:
            for line in f:
                parts = line.split()
                vocab.append(parts[0])
                vectors.append(list(map(float, parts[1:])))
                if limit is not None and len(vocab) >= limit:
                    log.info("Trimming vocabulary to %d" % limit)
                    break
        assert len(vocab) == len(vectors)
        return vocab, np.array(vectors)

    def __call__(self, word1, word2, exp=None):
        """
        Computes cosine similarity between these two
        :param word1: arg1
        :param word2: arg2
        :return: score between [0.0, 1.0]
        """
        assert ' ' not in word1
        assert ' ' not in word2
        if exp is None:
            exp = self.exp
        assert exp > 0
        vec1, vec2 = self.glove(word1), self.glove(word2)
        if vec1 is None or vec2 is None:
            # if one of them is missing
            return 1.0 if word1 == word2 else 0.0
        else:
            return (1.0 - cosine(vec1, vec2)) ** exp


def score_seqs(seq1, seq2, metric):
    if not seq1 or not seq2:
        return 0.0

    # Step iterate over all possible alignment
    long, short = copy(seq1), copy(seq2)
    if len(short) > len(long):
        long, short = short, long

    # TODO: To solve the general version of this problem
    # 1. https://en.wikipedia.org/wiki/Hopcroft–Karp_algorithm
    # 2. https://en.wikipedia.org/wiki/Hungarian_algorithm
    # Here I am assuming the shorter sequence to be of length one
    assert len(short) == 1

    cand_cluster = short[0]
    scores = [0.0] * len(long)
    for i in range(len(long)):
        match_cluster = long[i]
        scores[i] = max(metric(a, b) for a in cand_cluster for b in match_cluster)
    return max(scores) / len(long)


def score_all(inp, outp, metric, delim='\t', multi_mode=False, single_score=False):
    """
    Scores records from inp and writes to output
    :param inp: input to read records, usually an opened file
    :param outp: output to write the result, usually an opened file
    :param metric: metric for scoring
    :param delim: delimiter for splitting the records in the input
    :param multi_mode: treat columns as multiple words separated by spaces and
            each word is a group of synonyms separated by commas
    :return: None
    """

    def tokenize(string):
        tokens = string.split()
        return [tok.split(',') for tok in tokens]

    count = 0
    total = 0.0
    for line in inp:
        words = line.split(delim)
        if len(words) != 2:
            log.warning("Skip: %s" % line)
            continue
        word1, word2 = words[0].strip(), words[1].strip()
        if not multi_mode:
            score = metric(word1, word2)
        else:
            score = score_seqs(tokenize(word1), tokenize(word2), metric)
        total += score
        count += 1
        if not single_score:
            outp.write("%s%s%s%s%.4f\n" % (word1, delim, word2, delim, score))
    if single_score:
        outp.write("%.4f" % (total / count))
    log.info("Scored %d records" % count)


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(dest='metric', help='Metrics')

    # strict sub command
    sub_parsers.add_parser('strict', help='Strict match')

    # glove sub command
    glove_parser = sub_parsers.add_parser('glove', help='Cosine similarity of Glove Vectors')
    glove_parser.add_argument('-m', '--model', help='Model file', required=True)
    glove_parser.add_argument('-vs', '--vocab-size', help='Vocabulary size to trim (optional)', type=int)

    # global parser arguments
    parser.add_argument('in', nargs='?', help='Input file to read records. Default is STDIN',
                        type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('out', nargs='?', help='Output file to write result. Default is STDOUT',
                        type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-mm', '--multi-mode', help='Multi word matching mode, uses spaces to split words,'
                                                    ' commas(,) to split synonyms and tabs to split columns',
                        action='store_true', default=False)
    parser.add_argument('-avg', '--average-score', help='Single score by computing the average of all records',
                        action='store_true', default=False)

    args = vars(parser.parse_args())
    if args['metric'] == 'strict':
        metric = StrictMatch()
    elif args['metric'] == 'glove':
        metric = GloveCosine(args['model'], limit=args.get('vocab_size', None), exp=2)
    else:
        raise Exception('Unknown metric %s' % args['metric'])
    score_all(args['in'], args['out'], metric,
              multi_mode=args['multi_mode'],
              single_score=args['average_score'])

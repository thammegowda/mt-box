#!/usr/bin/env python

"""
Evaluator for Seq Splitter.

---

Author : Thamme Gowda
Created : Nov 30, 2017
"""

import sys
import logging as log
from seqsplit import SeqSplitter
from seqsplit.terminal_rule import TerminalSplitter

log.basicConfig(level=log.INFO)


def tag_line_breaks(records, tokenizer=None):
    """
    Tags all the tokens in records as one stream.
    It marks line endings as '1' others as 0
    :param records:
    :param tokenizer: tokenizer to be used, default is whitespace tokenizer
    :return: stream of tokens with 0 for inside tokens and 1 for sentence endings
    """
    for rec in records:
        toks = tokenizer(rec) if tokenizer else rec.strip().split()
        assert toks
        yield from ((t, 1 if i == len(toks) - 1 else 0) for i, t in enumerate(toks))


def fix_tokenization(src, ref):
    """
    A quick fix for extra tokenizations in references.
    :param src:
    :param ref:
    :return: source, reference , after aligning the tokens
    """

    def aligner(token, seq, idx):
        # Reference may vae split this source word into many parts
        buf = seq[idx][0]
        k = idx
        while buf != token and len(buf) < len(token) and k < len(seq):
            k += 1
            buf += seq[k][0]
        return k if buf == token else -1
    src_res, ref_res = [], []
    i, j = 0, 0
    while i < len(src) and j < len(ref):
        left, right = src[i], ref[j]
        error = src[i][0] != ref[j][0]
        if error:  # we have a problem!
            if len(src[i][0]) > len(ref[j][0]):
                # Reference may have split this source word into many parts
                new_j = aligner(src[i][0], ref, j)
                if new_j != -1:
                    log.info("SPLIT: %s --> %s" % (src[i][0], str(ref[j:new_j+1])))
                    parts = ref[j:new_j + 1]
                    right = (' '.join(p[0] for p in parts), min(1, sum(p[1] for p in parts)))
                    j = new_j
                    error = False
            else:
                # Reference may have combined a few words
                new_i = aligner(ref[j][0], src, i)
                if new_i != -1:
                    log.info("MERGE: %s --> %s" % (str(src[i: new_i+1]), ref[j][0]))
                    parts = src[i: new_i + 1]
                    left = (' '.join(p[0] for p in parts), min(1, sum(p[1] for p in parts)))
                    i = new_i
                    error = False

        if error:
            # try skipping one or two
            if src[i][0] == ref[j+1][0]:
                log.warning('Skip REF:%s' % ref[j][0])
                j += 1
                right = ref[j]
            elif src[i+1][0] == ref[j][0]:
                log.warning('Skip SRC:%s' % src[i][0])
                i += 1
                left = src[i]
            elif src[i+1][0] == ref[j+1][0]:
                log.warning('Skip SRC:%s  REF:%s' % (src[i][0], ref[j][0]))
                i += 1      # skip both src[i] and ref[j]
                j += 1
                left = src[i]
                right = ref[j]
            else:     # failed to align
                log.error("SRC:%s  REF:%s" % (src[max(0, i-3): min(len(src), i+4)], ref[max(0, j-3): min(len(ref), j+4)]))
                raise Exception('Failed to align SRC:%s with REF:%s' % (src[i][0], ref[j][0]))

        src_res.append(left)
        ref_res.append(right)
        i += 1
        j += 1
    if i < len(src):
        log.error('SRC has left over tokens')
    if j < len(ref):
        log.error('REF has left over tokens')

    assert len(src_res) == len(ref_res)
    return src_res, ref_res


def confusion_matrix(out, ref):
    """
    returns a confusion matrix.
    Interpretation (x,y) : 10 means 10 records which are marked 'x' in reference, but predicted as 'y'.
    Note that this interpretation is valid only when first argument is predictions and second argument is gold labels
    :param out:
    :param ref:
    :return:
    """
    assert len(out) == len(ref)
    tab = dict((x, 0) for x in ((0, 0), (0, 1), (1, 0), (1, 1)))
    print(len(out), len(ref))
    for i, ((pt, pred), (gt, gold)) in enumerate(zip(out, ref)):
        assert pt.replace(' ', '') == gt.replace(' ', ''), '%s -- %s' % (pt, gt)
        if pred != gold:
            #print("False Negative::")
            print('OUT:' + ' '.join(map(lambda x: x[0] + ('**' if x[1] else ''),  out[i-10:i+10])))
            print('REF:' + ' '.join(map(lambda x: x[0] + ('**' if x[1] else ''), ref[i - 10:i + 10])))
            print("===")
        tab[gold, pred] += 1
    return tab


def evaluate(src, ref, out, model=None):
    def read_lines(fptr):
        for line in fptr:
            line = line.strip()
            if line:
                yield line

    src_recs = list(read_lines(src))
    out_recs = list(read_lines(out))
    ref_recs = list(read_lines(ref))

    tokenizer = None
    if model:
        model = SeqSplitter.load(model)
        tokenizer = model.tokenize
    log.info("Recs   :Output:%s  Reference:%s" % (len(out_recs), len(ref_recs)))
    ref_toks = list(tag_line_breaks(ref_recs, tokenizer=tokenizer))
    out_toks = list(tag_line_breaks(out_recs, tokenizer=tokenizer))

    log.info("Tokens: Output:%s  Reference:%s" % (len(out_toks), len(ref_toks)))
    out_toks, ref_toks = fix_tokenization(out_toks, ref_toks)
    log.info("Tokens: Output:%s  Reference:%s" % (len(out_toks), len(ref_toks)))

    mat = confusion_matrix(out_toks, ref_toks)
    print('Confusion Matrix 1:', mat)
    print("Source already has %d line breaks. So, reducing them" % len(src_recs))
    mat[1, 1] -= len(src_recs)
    print('Confusion Matrix 2:', mat)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('-s', '--src', help='Source file', type=argparse.FileType('r'), required=True)
    p.add_argument('-r', '--ref', help='Reference file', type=argparse.FileType('r'), required=True)
    p.add_argument('-o', '--out', help='Splitter output file', type=argparse.FileType('r'), default=sys.stdin)
    p.add_argument('-m', '--model', help='Model. Used for tokenizing', required=False)
    evaluate(**vars(p.parse_args()))

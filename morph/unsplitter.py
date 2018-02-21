#!/usr/bin/env python
# Author =  Thamme Gowda
# Date = Feb 20, 2018
# Version 0.1

"""
When morfessor or BPE encoder is used, the words are split into multiple parts.
translation model might simply copy parts to target side, thus some parts might be copied.
This script attempts to identify parts, and when feasible it joins them.

Format:
 SOURCE SENTENCE<tab>SOURCE SPLIT SENTENCE<tab>TARGET SENTENCE


"""

import logging as log
log.basicConfig(level=log.INFO)


def un_split(seq1, seq2, drop_chars=''):
    """Finds alignment with whole words and parts (in same order)."""
    assert len(seq2) >= len(seq1)  # the words in seq1 are split to get seq2, the length of seq2 should be bigger
    # figure out the split alignments
    l, r = 0, 0  # left is original seq, right is split sequence
    splits = []
    while l < len(seq1) and r < len(seq2):
        word = seq1[l]
        buf = ""
        i = r
        while i < len(seq2):
            buf += seq2[i].strip()
            if drop_chars:
                # any replacements such as @@ or - introduced to splits
                buf = buf.replace(drop_chars, '')
            i += 1
            if buf == word:
                break
            elif len(buf) > len(word):   # exceeded len, but didnt get the original word
                raise Exception(f"Cant find split of word {word}")
            # else : keep joining splits

        assert word == buf
        splits.append(tuple(seq2[r: i]))
        r = i
        l += 1
    assert len(seq1) == len(splits)
    return splits


def replace_whole(orig, src, tgt, drop_chars):
    """Replaces parts with whole"""
    splits = un_split(orig, src, drop_chars)
    rev_lookup = {}
    for w, ss in zip(orig, splits):
        for s in ss:
            if rev_lookup.get(s, w) != w:
                # FIXME : preserve positional info
                log.warning(f"Ambiguous :: {s} is either from {w} or {rev_lookup[s]}")
            rev_lookup[s] = w
    src_vocab = set(src)
    orig_vocab = set(orig)
    result = []
    for i, word in enumerate(tgt):
        if word in src_vocab:  # this was copied
            if word in orig_vocab:  # this is a full word
                result.append(word)
            else:    # this is a split word
                tgt_word = rev_lookup[word]
                if result and result[-1] == tgt_word:  # already copied, do nothing
                    pass
                else:
                    result.append(tgt_word)
        else:
            # it was translated
            result.append(word)
    return result


def run(inp, outp, drop_chars):
    """
    Un split
    :param outp:
    :return:
    """
    for line in inp:
        cols = line.strip().split('\t')
        assert len(cols) == 3
        orig, src, tgt = tuple(x.split() for x in cols)
        # print(orig, src, tgt)
        result = replace_whole(orig, src, tgt, drop_chars)
        result = ' '.join(result)
        outp.write(result)
        outp.write('\n')


if __name__ == '__main__':
    import argparse, sys
    p = argparse.ArgumentParser()
    p.add_argument('-in', nargs='?', help="""Input (SOURCE SENTENCE<tab>SOURCE SPLIT SENTENCE<tab>TARGET SENTENCE""",
                   type=argparse.FileType('r'), default=sys.stdin)
    p.add_argument('-out', nargs='?', help="Output file to write data.", type=argparse.FileType('w'),
                   default=sys.stdout)
    p.add_argument('-drop', nargs='?', help="Drop characters such as '-', '@@', that are affixed during the split.")
    args = vars(p.parse_args())
    run(args['in'], args['out'], args['drop'])
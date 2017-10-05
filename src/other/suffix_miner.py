from argparse import ArgumentParser
import sys

alphabet = 'abcdefghijklmnopqrstuvwxyz'


def read_file(path, delim='\t'):
    with open(path) as f:
        return [line.strip().split(delim) for line in f]


def find_suffix(word1, word2):
    last = -1
    for i in range(min(len(word1), len(word2))):
        if word1[i] != word2[i]:
            break
        last = i
    root = word1[:last+1]
    suff1 = word1[last+1:]
    suff2 = word2[last+1:]
    return root, suff1, suff2


def normalize_sounds(word):
    for char in alphabet:
        word = word.replace(char+char, char)
    return word


def mine_suffixes(recs):
    recs = (rec for rec in recs if len(rec) == 2)
    recs = ((normalize_sounds(rec[0]), normalize_sounds(rec[1])) for rec in recs)
    for lemma, inflection in recs:
        root, suf1, suf2 = find_suffix(lemma, inflection)
        if root and (suf1 or suf2):
            print("%s\t%s\t%s" % (root, suf1, suf2))


if __name__ == '__main__':
    sys.argv = ['', '-i', '/Users/tg/work/isi/oov/workspace/oromo-oov/oromo-lemmas.tsv']
    parser = ArgumentParser()
    parser.add_argument('-i', help='File having "lemma\tinflection"', required=True)
    args = vars(parser.parse_args())
    recs = read_file(args['i'])
    mine_suffixes(recs)

#!/usr/bin/env python3
"""
Normalizes spellings of words of non-english languages that use latin script.


author: Thamme Gowda
version: 0.1
date: August 21, 2017
"""
import sys
from argparse import ArgumentParser
import codecs
import re


alphabet = 'abcdefghijklmnopqrstuvwxyz'
patterns = [r"([{0}{1}])[{0}{1}]+" .format(ch.upper(), ch) for ch in alphabet]
replacement_pattern = r'\1'   # the first character in whichever the case it appears


def read_tokens(path, tokenize=True):
    """
    Reads tokens from a file to set
    :param path: path to file
    :param tokenize: should the lines be tokenized by white space?
    :return: set of tokens
    """
    with codecs.open(path) as f:
        lines = (line.strip() for line in f)
        tokens = set()
        if tokenize:
            lines = (line.split() for line in lines)
            for parts in lines:
                tokens.update(parts)
        else:
            tokens.update(lines)
    return tokens


def normalize_word(word):
    """
    Normalizes a word by replacing repeated characters
    :param word:
    :return:
    """
    for p in patterns:
        word = re.sub(p, replacement_pattern, word)
    return word


def is_copyme(word):
    """
    returns true if the tokens be copied to output
    :param word:
    :return:
    """
    if word[0] == '@' or word[0] == '#':  # twitter handle or hashtag
        return True
    if '@' in word:  # simple and fast email checker
        return True
    if '://' in word:  # simple and fast url checker
        return True


def normalize_stdio(copy_me_tokens, ignore_case=False):
    """
    Normalizes the text in standard input and writes it to standard output
    :param copy_me_tokens:  set of tokens which should be copied
    :param ignore_case:  should the lookup of tokens in copy_me set be case insensitive?
    :return: None, everything goes to STDOUT
    """
    if ignore_case:
        copy_me_tokens = set([tok.lower() for tok in copy_me_tokens])
    for line in sys.stdin:
        line = line.strip()
        result = []
        for tok in line.split():
            lookup_tok = tok.lower() if ignore_case else tok
            if lookup_tok in copy_me_tokens or is_copyme(tok):
                result.append(tok)
            else:
                result.append(normalize_word(tok))
        out_line = ' '.join(result)
        print(out_line)

if __name__ == '__main__':
    parser = ArgumentParser(description='Oromo Script normalizer')
    parser.add_argument('-v', '--vocab', help='English Vocabulary', required=True)
    parser.add_argument('-t', '--tokenize', help='Tokenize english Vocabulary', action='store_true', default=False)
    parser.add_argument('-i', '--ignore-case', help='Ignore case while looking up the tokens in vocabulary',
                        action='store_true', default=False)
    args = vars(parser.parse_args())
    tokens = read_tokens(args['vocab'], args['tokenize'])
    normalize_stdio(tokens, args['ignore_case'])
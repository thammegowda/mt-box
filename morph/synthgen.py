"""
Synthetic Language Generator.

"""
__author__ = 'Thamme Gowda'
__created__ = 'February 15, 2018'
__version__ = '0.1'

import string
import logging as log
from collections import defaultdict
import numpy as np
import pickle
import random


log.basicConfig(level=log.INFO)


class Joiner(object):
    """Word joiner model.
    There are 8 types of operations
        1. Concat morphemes
        2. Add one or more chars at the join
        3. Remove one or more chars on the left side ending
        4. Remove one or chars on the right side beginning
        5. Remove both one or more chars on both the sides
        6. Modify Left side ending chars
        7. Modify Right side beginning chars
        8. Modify both (remove both and insert)
    """

    def __init__(self, types={1}):
        self.types = types      # Supported types

    def type1(self, l, r):
        """Simple concatenation"""
        return l + r

    def type2(self, l, r):
        """Add some chars"""
        raise Exception('Not implemented')

    def type3(self, l, r):
        """Remove some chars on left side"""
        raise Exception('Not implemented')

    def type4(self, l, r):
        """Remove some chars on right side"""
        raise Exception('Not implemented')

    def type5(self, l, r):
        """Remove some chars on both side"""
        raise Exception('Not implemented')

    def type6(self, l, r):
        """Modify some chars on left side"""
        raise Exception('Not implemented')

    def type7(self, l, r):
        """Modify some chars on right side"""
        raise Exception('Not implemented')

    def type8(self, l, r):
        """Modify some chars on both side"""
        raise Exception('Not implemented')

    def join(self, l, r):
        # TODO: support other types of joins
        return self.type1(l, r), 1


class SyntheticLang(object):
    """a synthetic language generator with morphologically inflected vocabulary."""

    def __init__(self, alphabet_size=15, num_morphs=1000, min_morph_len=2, max_morph_len=8, num_words=3000):
        assert num_morphs > 0
        assert num_words > num_morphs
        assert alphabet_size <= len(string.ascii_letters)

        self.alphabet_size = alphabet_size
        self.alphabet = list(string.ascii_letters[:alphabet_size])
        self.num_morphs = num_morphs
        self.max_morph_len = max_morph_len
        self.min_morph_len = min_morph_len
        self.num_words = num_words

        # using exponential distribution for characters
        sample = np.random.exponential(scale=1.5, size=alphabet_size)
        self.char_freq_distr = sample / sum(sample)

        sample = np.random.random(size=max_morph_len+1)
        for i in range(min_morph_len):
            sample[i] = 0   # make zero probability
        self.word_len_distr = sample / sum(sample)

        self.morphs = self.generate_morphs(self.num_morphs)
        self.joiner = Joiner(types={1})         # only type 1 for now
        self.words = self.generate_words(list(self.morphs.keys()), self.num_words)

    def generate_morphs(self, count):
        res = defaultdict(int)
        lengths = list(range(self.max_morph_len + 1))

        while len(res) < count:
            morph_len = np.random.choice(lengths, replace=False, p=self.word_len_distr)
            chars = np.random.choice(self.alphabet, replace=False, p=self.char_freq_distr, size=morph_len)
            morph = ''.join(chars)
            res[morph] += 1
        return res

    def generate_words(self, morphs, count):

        words = {}
        word_list = []   # for making a random choice
        fertility = defaultdict(int)
        assert type(morphs) is list

        # randomly select some morphemes as prefixes or suffixes.
        # these morphemes will not appear in final vocabulary as independent words
        num_affix = int(max(15.0, 0.05 * len(morphs)))
        for morph in morphs:
            words[morph] = ((morph, ''), 0)    # 0 = atomic morpheme
            word_list.append(morph)

        while len(words) < count + num_affix:
            left = np.random.choice(word_list)
            right = np.random.choice(word_list)
            compound, morph_type = self.joiner.join(left, right)
            if len(compound) > 3 * self.max_morph_len:
                continue    # too long
            if compound not in words:
                words[compound] = ((left, right), morph_type)
                word_list.append(compound)
                fertility[left] += 1
                fertility[right] += 1
            else:
                (old_l, old_r), old_type = words[compound]
                if old_l != left or old_r != right or old_type != morph_type:
                    # great! now we have ambiguity too
                    log.warning(f"Ambiguous construct: {compound} = {old_l}+{old_r} (type{old_type}) "
                                f" = {left}+{right} (type{morph_type}) ")

        # these wont go to vocab as independent words
        affixes = sorted(fertility.items(), key=lambda x: x[1], reverse=True)[:num_affix * 2]
        affixes = random.sample(affixes, num_affix)
        for affix, ft in affixes:
                del words[affix]
        return words

    def save(self, path):
        log.info(f"Writing to {path}")
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    def write_words(self, path):
        with open(path, 'w') as f:
            for w, ((l, r), t) in self.words.items():
                f.write(f'{w}\t{t}\t{l}\t{r}\n')


if __name__ == '__main__':
    lang = SyntheticLang(alphabet_size=15, num_morphs=1000, num_words=3000)
    lang.write_words('words.txt')

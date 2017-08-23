from codecs import open as copen
from argparse import ArgumentParser
import random
from elisa import parse_elisa
import re
import gzip, codecs
import logging as log
import sys
from oromo_norm import normalize_word, is_copyme

log.basicConfig(level=log.INFO)


oro_suffixes = ['anif', 'anis', 'dhaf', 'dhan', 'tani', 'icha', 'ichi', 'tif', 'itu', 'ati', 'dha', 'ine', 'era', 'ina',
            'tan', 'tin', 'oni', 'ani', 'ota', 'chu', 'ef', 'nu', 'en', 'le', 'na', 'ni', 'ne', 'in', 'ta', 'su',
            'te', 'an', 'fi', 'tu', 'ti', "'u", 's', 'o', 'i', 'f', 'e', 'n', 'a', 'u']

'''
NOTES: TODO:
   1. Right now a random item is chosen from synonyms. Chose a single phrase word
   2. Use the awesome names index you have built using wikipedia dataset
'''


def dump_stream(recs, path):
    """
    writes lines to file
    :param recs: stream of lines
    :param path: file path
    :return:
    """
    with copen(path, 'w', 'utf-8') as out:
        for rec in recs:
            out.write(rec)
            out.write('\n')


class OOVTranslator(object):

    def __init__(self, dict_file):
        self.f2e = {}
        count = 0
        skipped = 0
        self.eng = set()
        with copen(dict_file) as file:
            for line in file:
                parts = line.strip().split("\t")
                if len(parts) != 3:
                    log.warning(">Skip: %s" % line)
                    skipped += 1
                    continue
                p, f, e = parts
                f, e = f.strip(), e.strip()
                self.eng.add(e)
                if f not in self.f2e:
                    self.f2e[f] = set()
                count += 1
                self.f2e[f].add(e)
        log.info("Skipped %d lines" % skipped)
        log.info("Found %d english words" % len(self.eng))
        for k in self.f2e.keys():
            self.f2e[k] = list(self.f2e[k])
        log.info("> Mappings has %d words to %d english words" % (len(self.f2e), count))

        # normalized dictionary
        self.alphabet = 'abcdefghijklmnopqrstuvwxyz'
        self.f2e_norm = {}
        for f in self.f2e.keys():
            f_ = normalize_word(f)
            if f_ not in self.f2e_norm:
                self.f2e_norm[f_] = set()
            self.f2e_norm[f_].update(self.f2e[f])
        for k in self.f2e_norm.keys():
            self.f2e_norm[k] = list(self.f2e_norm[k])
        log.info("> Normalized Dictionary has %d foreign words to %d english words map" % (len(self.f2e), count))

        # stemmed dictionary
        self.f2e_stem = {}
        for f in self.f2e_norm.keys():
            f_ = self.stem(f)
            if f_ not in self.f2e_stem:
                self.f2e_stem[f_] = set()
            self.f2e_stem[f_].update(self.f2e_norm[f])
        for k in self.f2e_stem.keys():
            self.f2e_stem[k] = list(self.f2e_stem[k])
        log.info("> Stemmed-Normalized Dictionary has %d foreign words to %d english words map" % (len(self.f2e), count))

    def stem(self, word, level=1, maxlevel=1):
        for suff in oro_suffixes:
            if word.endswith(suff):
                word = re.sub(r'%s$' % suff, '', word)
                # FIXME: this stemmer assumes that there is only one suffix.
                #  But in reality a word can be broken into multiple parts
                if level < maxlevel:
                    self.stem(word, level+1)
                break
        return word

    def get_best(self, items):
        for i in range(len(items)):
            best = random.choice(items)
            if ' ' not in best: # no space ==> unigram
                return best
        return random.choice(items)

    def translate_oow(self, word, ctx=None, pos=None):
        if word in self.eng:
            return word             # this is already translated

        if word in self.f2e:        # word is in dictionary
            return self.get_best(self.f2e[word])

        if is_copyme(word)

        word_norm = self.normalize_sounds(word)
        if word_norm in self.f2e_norm:   # word in normalized dictionary
            log.debug('NORM HIT: %s found as normalized  %s in dictionary' % (word, word_norm))
            return self.get_best(self.f2e_norm[word_norm])

        word_stem = self.stem(word_norm)
        if word_stem in self.f2e_stem:  # word in stemmed-normalized dictionary
            log.debug('STEM HIT: %s found as stem  %s in dictionary' % (word, word_stem))
            return self.get_best(self.f2e_stem[word_stem])

        # all upper case, like NASA, USA or UNICEF
        if word.isupper() and 2 < len(word) < 6:
            return word

        # TODO: name lookup

        log.debug("OOV MISS: Couldn't translate OOV word: %s", word)
        return word

    def translate_segment(self, seg):
        res = []
        idx = 0
        for tok, tag in seg.get_tokens():
            if tag == 'UNK' or tag == 'IDEN' and not self.is_copyme(tok):
                trans = self.translate_oow(tok, seg, idx)
                res.append(trans)
            else:
                res.append(tok)
            idx += 1
        return res

    def post_process(self, seg, capitalize=True):
        seq = self.translate_segment(seg)
        sent = ' '.join(seq)
        if capitalize:
            # capitalize first alphabet in sentence
            firstchar = 0
            while firstchar < len(sent) and not sent[firstchar].isalpha():
                firstchar += 1
            if firstchar < len(sent):
                sent = sent[:firstchar] + sent[firstchar].upper() + sent[firstchar+1:]
        return sent

if __name__ == '__main__':
    parser = ArgumentParser(description='Out of Vocabulary Post Processor (for ELISA)')
    parser.add_argument('-i', '--in', help='ELISA XML file', required=True)
    parser.add_argument('-o', '--out', help='OUTPUT FILE', required=True)
    parser.add_argument('-d', '--dict', help='Dictionary File', required=True)

    args = vars(parser.parse_args())
    oov_trans = OOVTranslator(args['dict'])

    segs = parse_elisa(args['in'])
    sents = map(oov_trans.post_process, segs)
    dump_stream(sents, args['out'])
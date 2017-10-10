#!/usr/bin/env python
"""
Translation Table Data Structure
"""
import logging as log
import re
import os
import glob
import pickle
from ds import Trie

log.basicConfig(level=log.INFO)
__author__ = 'Thamme Gowda'
__created__ = 'October 3, 2017'
__version__ = '0.1'


class TTable(object):
    """
    Translation Table - alignment information from Giza Aligner
    """

    def __init__(self, giza_out_dir, src, tgt):
        """
        creates a translational table
        :param giza_out_dir: path to giza output
        :param src: source language code
        :param tgt: target language code
        """
        self.src = src
        self.tgt = tgt
        self.dir = giza_out_dir
        assert os.path.exists(self.dir)

        src_vcb = glob.glob(self.dir + '/*.%s.vcb' % src)
        tgt_vcb = glob.glob(self.dir + '/*.%s.vcb' % tgt)
        log.info("Vocabulary Files: SRC: %s; TGT:%s" % (src_vcb, tgt_vcb))
        assert 1 == len(src_vcb) == len(tgt_vcb)
        src_vcb, tgt_vcb = src_vcb[0], tgt_vcb[0]
        self.src_id2tok, self.src_freq = TTable.load_vocab(src_vcb)
        self.tgt_id2tok, self.tgt_freq = TTable.load_vocab(tgt_vcb)
        self.src_tok2id, self.tgt_tok2id = TTable.reverse_map(self.src_id2tok), TTable.reverse_map(self.tgt_id2tok)
        log.info("Vocabulary Size: SRC: %d; TGT:%d" % (len(self.src_id2tok), len(self.tgt_id2tok)))

        ttab_file = glob.glob(self.dir + '/*normal.t[0-9]*.final')
        inv_ttab_file = glob.glob(self.dir + '/*invers.t[0-9]*.final')
        assert ttab_file
        self.ttab = self.read_ttab(ttab_file[0], self.src_id2tok, self.tgt_id2tok)
        self.inv_ttab = self.read_ttab(inv_ttab_file[0], self.tgt_id2tok, self.src_id2tok) if inv_ttab_file else {}
        log.info("T-Tab Size: Normal: %d; inverse:%d" % (len(self.ttab), len(self.inv_ttab)))

        # prefix trie
        self.src_trie = Trie.build(self.src_tok2id.keys())
        self.tgt_trie = Trie.build(self.tgt_tok2id.keys())
        log.info("Trie size: SRC: %d; TGT:%d" % (len(self.src_trie), len(self.tgt_trie)))

    def store_at(self, path):
        log.info('storing at %s' % path)
        pickle.dump(self, open(path, 'wb'))

    def vocab_match(self, pattern, source=True):
        # TODO: use a trie to support prefix match
        vocab = self.src_tok2id.keys() if source else self.tgt_tok2id.keys()
        yield from (key for key in vocab if key and re.match(pattern, key))

    def longest_src_prefix(self, term):
        return self.src_trie.prefix_match(term)

    @staticmethod
    def reverse_map(data, one_to_one=True):
        rev = {}
        for k, v in data.items():
            if one_to_one:
                assert v not in rev
            rev[v] = k
        return rev

    @staticmethod
    def load_from(path):
        log.info("Loading from %s" % path)
        ttab = pickle.load(open(path, 'rb'))
        log.info("Vocabulary Size: SRC: %d; TGT:%d" % (len(ttab.src_id2tok), len(ttab.tgt_id2tok)))
        log.info("T-Tab Size: Normal: %d; inverse:%d" % (len(ttab.ttab), len(ttab.inv_ttab)))
        log.info("Prefix Trie Size: SRC: %d; TGT:%d" % (len(ttab.src_trie), len(ttab.tgt_trie)))
        return ttab

    @staticmethod
    def load_vocab(path, augment=((0, None, None),)):
        """
        loads vocabulary
        :param path: path of vocabulary
        :param augment: additional data to be augmented. Example = [(0, None), (1, 'UNK')]
        :return: dict, dict - the first one has id to token mapping, the second one has id to frequency
        """
        with open(path) as f:
            id2tok = {}
            freq = {}
            for line in f.readlines():
                line = line.strip()
                if not line:
                    continue
                idx, tok, count = line.split()
                idx, count = int(idx), int(count)
                id2tok[idx] = tok
                freq[idx] = count
            if augment:
                for idx, tok, count in augment:
                    assert idx not in id2tok
                    id2tok[idx] = tok
                    freq[idx] = count
            return id2tok, freq

    @staticmethod
    def read_ttab(path, idx1, idx2):
        ttab = {}
        with open(path) as f:
            for line in f:
                src_id, tgt_id, prob = line.split()
                src_id, tgt_id, prob = int(src_id), int(tgt_id), float(prob)
                src_tok, tgt_tok = idx1[src_id], idx2[tgt_id]
                if src_tok not in ttab:
                    ttab[src_tok] = []
                ttab[src_tok].append((tgt_tok, prob))
        # sort
        for src_tok, cands in ttab.items():
            ttab[src_tok] = sorted(cands, key=lambda x: x[1], reverse=True)
        return ttab


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description='T-Table compressor')
    parser.add_argument('-g', '--giza', help='Giza++ output directory path', required=True)
    parser.add_argument('-s', '--src', help='Source language code. Example: esp', required=True)
    parser.add_argument('-t', '--tgt', help='Target language code. Example: eng', required=True)
    parser.add_argument('-o', '--out', help='Store the compressed T-Tab at this path', required=True)
    args = vars(parser.parse_args())
    ttab = TTable(args['giza'], src=args['src'], tgt=args['tgt'])
    out = args['out']
    if not out.endswith('.pkl') and not out.endswith('.pickle'):
        out += '.pkl'
    ttab.store_at(out)

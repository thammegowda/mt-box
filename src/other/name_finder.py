
# -*- coding: utf-8 -*-

import codecs
import logging as log
import sys
from argparse import ArgumentParser

from other import oromo_stemmer
from solr import Solr

log.basicConfig(level=log.INFO)


def stem(word):
    return oromo_stemmer.oromo_stem_line(word, oromo_stemmer.ulf_pttrn2, oromo_stemmer.trim_pttrn)


class NameFinder(object):

    def __init__(self, solr, stem_func=None):
        self.solr = solr
        self.stem = stem_func
        self.cache = {}

    @staticmethod
    def top_down_grams(phrase, max_grams=10):
        for size in range(min(max_grams, len(phrase)), 0, -1):
            for start in range(0, len(phrase) - size + 1):
                yield start, phrase[start: start + size]

    def greedy_search(self, phrase):
        grams = NameFinder.top_down_grams(phrase)

        for start, candidate_toks in grams:
            if start == 0:
                pass # shift down size --> reset state
            candidate_phrase = ' '.join(candidate_toks)
            # TODO: implement this

    def beam(self, group):
        if self.stem:
            stemmed = list(map(self.stem, group))
            log.debug("%s --> %s" % (group, stemmed))
            group = stemmed
        candidates = []
        candidates.extend(group)
        # TODO: use n grams
        if len(group) > 1:
            candidates.append(" ".join(group))
        for tok in candidates:
            results, is_new = self.lookup(tok)
            if results and is_new:
                    results = [(r['name'], r['score']) for r in results]
                    print('%s --> %s' % (tok, results))

    def lookup(self, word):
        is_new = False
        if word not in self.cache:
            res = solr.get_top("name_bmpm_s:\"%s\"" % word, rows=5, fl='name,score', sort='score desc,len asc')
            results = None
            if res and res['numFound'] > 0:
                results = res['docs']
            self.cache[word] = results
            is_new = True
        return self.cache[word], is_new

    def scan_names(self, line):
        toks = line.split()
        groups = []   # group based on title case token groups
        spanning = False
        log.debug(line)
        for tok in toks:
            if tok[0].isupper():
                if not spanning:
                    groups.append([])
                groups[-1].append(tok)
                spanning = True
            else:
                spanning = False
        return groups


def catch_names(path, finder):
    with codecs.open(path, 'r', 'utf-8') as f:
        for line in f:
            line = line.strip()
            groups = finder.scan_names(line)
            for group in groups:
                finder.beam(group)


if __name__ == '__main__':
    sys.argv = ['', '-in', '../data/set1.source.tok', '-solr', 'http://localhost:8983/solr/name']
    p = ArgumentParser()
    p.add_argument("-in", required=True, help="Input File.")
    p.add_argument("-solr", required=True, help="Solr URL. Eg:http://localhost:8983/solr/name")
    args = vars(p.parse_args())
    solr = Solr(args['solr'])
    finder = NameFinder(solr, stem_func=stem)
    catch_names(args['in'], finder)
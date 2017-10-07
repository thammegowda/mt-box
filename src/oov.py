
"""
Out of Vocabulary Translator
"""

from collections import defaultdict
from nltk.corpus import wordnet as wn
import numpy as np
import logging as log
from pprint import pprint
import os
import sys
from giza import TTable
import codecs

__author__ = 'Thamme Gowda'
__date__ = 'October 6, 2017'


log.basicConfig(level=log.INFO)


def get_synonyms(word):
    """
    Gen Synonyms of the given word
    :param word: word whose synonyms are needed
    :return: set of synonyms
    """
    word = word.lower()
    syns = set()
    for synset in wn.synsets(word):
        syns.update(lemma.name() for lemma in synset.lemmas())
    syns.add(word)
    return syns


def syn_matrix(words, strategy='direct'):
    """
    Builds Synonym Matrix
    :param words: list of words
    :param strategy: scoring strategy {'direct', 'transitive'}
            direct - two words are scored if one word is synonym of other. Possible scores : {0,1,2}
            transitive - two words are grouped if they are direct synonyms or transitive synonyms.
                        Possible scores: [0, 1, 2, ....]
    :return: table of n x n
    """
    allowed = {'direct', 'transitive'}
    if strategy not in allowed:
        raise Exception("Allowed strategies: %s" % allowed)
    n = len(words)
    syns = defaultdict()
    for key in words:
        syns[key] = get_synonyms(key)
    table = np.zeros((n, n), dtype=int)
    for i in range(n):
        table[i, i] = len(syns[words[i]])
        for j in range(i):
            if strategy == 'direct':
                score = sum([words[i] in syns[words[j]],
                             words[j] in syns[words[i]]])
            elif strategy == 'transitive':
                score = len(syns[words[i]] & syns[words[j]])
            else:
                raise Exception('Strategy "%s" not implemented' % strategy)
            table[i, j] = table[j, i] = score
    return table


def merge_synonyms(keys):
    """
    Merges words into clusters based on synonym property.
    If two words are synonyms, then they belong to same cluster
    """
    n = len(keys)
    table = syn_matrix(keys)
    # TODO: assert symmetry in table
    assert table.shape == (n, n)

    def max_overlap(idx):
        cands = [(table[idx, j], j) for j in range(idx)]
        cands = sorted(cands, reverse=True)
        if cands and cands[0][0] > 0:
            return cands[0][1]
        # not found
        return idx

    shrink = {}
    for i in range(n):
        shrink[i] = max_overlap(i)
        shrink[i] = shrink[shrink[i]]  # transitive mapping
    shrinked = defaultdict(set)
    for i in range(n):
        shrinked[shrink[i]].add(i)
    clusters = [[keys[i] for i in s] for s in shrinked.values()]
    return clusters, shrink


class OOVTranslator(object):

    def __init__(self, ttab):
        self.ttab = ttab

    def translate(self, word):
        return word


class SuffixTranslator(OOVTranslator):

    def translate(self, word):
        res, _, _ = self.prefix_match(word)
        return res

    def prefix_match(self, term, cluster=True, inverse_wt=0.5, verbose=False):
        ttab = self.ttab
        for i in range(len(term), int(len(term) / 2.0), -1):
            qry = term[:i] + ".*"
            neighbors = list(ttab.vocab_match(qry))
            if neighbors:
                neighbors = set(neighbors)
                # step: get candidate probabilities and candidate in degree
                cands = defaultdict(float)
                indegree = defaultdict(int)
                for neigh in neighbors:
                    if verbose:
                        print('== %s --> %s --> %s ==' % (term, qry, neigh))
                        pprint([r for r in ttab.ttab[neigh] if r[1] >= 0.1])
                    for cand, prob in ttab.ttab[neigh]:
                        cands[cand] += prob
                        indegree[cand] += 1
                N = len(cands)
                assert N == len(indegree)
                tgt_words = list(cands.keys())

                # Step: Normalize scores for candidates
                for key in tgt_words:
                    cands[key] /= N
                    cands[key] += 1. * indegree[key] / N

                if cluster:
                    # Step: resolve synonyms, merge candidates
                    clusters, reduction = merge_synonyms(tgt_words)
                    tgt_clster_names = {}
                    for from_, to in reduction.items():
                        if to not in tgt_clster_names:
                            tgt_clster_names[to] = tgt_words[from_]
                        else:
                            tgt_clster_names[to] += ',' + tgt_words[from_]
                    clusters = defaultdict(set)
                    for from_, to in reduction.items():
                        clusters[tgt_clster_names[to]].add(tgt_words[from_])

                    # step: cluster wise aggregation
                    agg_scores = defaultdict(float)
                    for i, key in enumerate(tgt_words):
                        agg_scores[tgt_clster_names[reduction[i]]] += cands[key]
                    cands = agg_scores
                else:
                    clusters = defaultdict(set)
                    for tgt_word in tgt_words:
                        clusters[tgt_word].add(tgt_word)

                # Step: ranking based on inverse t-table and weighting
                if inverse_wt > 0:
                    assert inverse_wt <= 1.0
                    # linear combination
                    fwd_wt = 1.0 - inverse_wt
                    inv_rank = self.inverse_rank(clusters, neighbors)
                    if verbose:
                        print("Inverse Rank")
                        pprint(inv_rank)
                    for name, score in cands.items():
                        cands[name] *= fwd_wt  # weightage for the forward score
                        cands[name] += inverse_wt * inv_rank[name]  # weightage for the inverse score

                # Step: final sorting
                cands = sorted(cands.items(), key=lambda x: x[1], reverse=True)
                return cands, neighbors, clusters
        return None, None, None

    def inverse_rank(self, clusters, neighbors, normalize=False):
        rank = defaultdict(float)
        n = 0
        for clstr_name, clstr in clusters.items():
            n += len(clstr)
            for word in clstr:
                for f_word, prob in self.ttab.inv_ttab[word]:
                    if f_word in neighbors:
                        rank[clstr_name] += prob
        if normalize:
            for name in clusters:
                rank[name] /= n
        return rank


def read_column(path, col=0, delim=None):
    """
    reads a column from columnized file such as CSV or TSV. the default args are tuned to read lines in text file.
    Note - this doesnt care for quotes!
    :param path: path to file
    :param col: column to read from file. it can be integer or list of numbers.
        When it is a list the returned columns are sorted in increasing order without bothering the order given in this list/
    :param delim: delimiter for splitting
    :return:
    """
    with codecs.open(path) as f:
        for line in f:
            res = line.strip()
            if not res:
                continue
            if delim:
                res = res.split(delim)
                if type(col) is int:
                    res = res[col]
                else:
                    res = [x for i, x in enumerate(res) if i in col]
            yield res

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-t', '--ttab', required=True, help='Translation Table path')
    parser.add_argument('-i', '--in', help='Input word list', required=True)
    args = vars(parser.parse_args())
    ttab = TTable.load_from(args['ttab'])
    words = list(read_column(args['in'], delim='\t', col=[0, 1]))
    trans = SuffixTranslator(ttab)
    for f_w, e_w, in words:
        res = trans.translate(f_w.lower())
        if res:
            res = res[:2]
        print("%s \t %s \t %s" % (f_w, e_w, res))




"""
Custom Data Structures

1. Trie - for prefix matching
"""

import logging as log

__author__ = 'Thamme Gowda'
__created__ = 'October 9, 2017'
__version__ = '0.1'
log.basicConfig(level=log.INFO)


class Trie(object):
    """
    Trie data structure for fast suffix matching
    """
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.kids = {}
        self.is_term = False
        self.count = 0

    def add_word(self, word, pos=0):
        self.count += 1
        if pos >= len(word):
            self.is_term = True
            return
        ch = word[pos]
        if ch not in self.kids:
            self.kids[ch] = Trie(ch, self)
        self.kids[ch].add_word(word, pos + 1)

    def prefix_match(self, word, pos=0):
        # base case: reached the end or no more match possible
        if pos == len(word) or word[pos] not in self.kids:
            return self, word[pos:]
        else:
            # recursive case : advance the position
            return self.kids[word[pos]].prefix_match(word, pos+1)

    def is_terminal(self, word, pos=0):
        if pos == len(word):
            return self.is_term
        ch = word[pos]
        if ch not in self.kids:
            return False
        return self.kids[ch].is_terminal(word, pos + 1)

    def get_path(self):
        txt = ''
        n = self
        while n:
            txt = n.name + txt
            n = n.parent
        return txt

    def terminal_children(self):
        if self.is_term:
            yield self
        for k in self.kids.values():
            yield from k.terminal_children()

    def __repr__(self):
        return self.get_path() + ('*' if self.is_term else '')

    def __str__(self):
        return self.get_path()[1:]

    def __len__(self):
        return self.count

    @staticmethod
    def build(words):
        root = Trie('/', None)
        for word in words:
            if word is not None:
                root.add_word(word)
        return root

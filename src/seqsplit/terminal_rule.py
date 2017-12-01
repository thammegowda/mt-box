#!/usr/bin/env python
"""
# Usage :
    # Train
    $ cat  <train_dir>/*.txt | python ./src/seqsplit/terminal_rule.py learn ssplit-1B-rules.pkl -vv -ci
    # Split
    $ cat  <test_dir>/*.txt | python ./src/seqsplit/terminal_rule.py split ssplit-1B-rules.pkl

---
Author  : Thamme Gowda
Created : Nov 29, 2017
"""

from collections import defaultdict
from seqsplit import SeqSplitter



class TerminalSplitter(SeqSplitter):

    class Marker(object):

        def __init__(self, name, context=(-1,)):
            self.name = name
            self.exceptions = dict((ctx, defaultdict(int)) for ctx in context)

    """
    Splits sequence based on terminal tokens.
    It learns exceptions using context,
    i.e. it tries to avoid false positive when given terminal tokens are treated as sentence markers.
    """
    def __init__(self, terminals=('.', '!', '?'), context=(-1,), min_observations=2, nocase=True):
        self.version = 1.0

        self.terminals = dict((t, self.Marker(t, context)) for t in terminals)
        self.min_obs = min_observations      # an exception must be seen at least 2 times
        self.other_terminals = defaultdict(int)
        self.nocase = nocase

    def learn(self, seqs, verbose=False):
        count = 0
        for seq in seqs:
            count += 1
            false_pos = [(idx, tok) for idx, tok in enumerate(seq)
                         if tok in self.terminals]

            # learn exceptions from false positives
            for idx, tok in false_pos:
                for rel_idx in self.terminals[tok].exceptions:
                    tru_idx = rel_idx + idx
                    if 0 <= tru_idx < len(seq):
                        # add to exception if inside seq (False Positive), subtract if at the ending (True Positive)
                        delta = -1 if idx == len(seq) - 1 else +1
                        self.terminals[tok].exceptions[rel_idx][seq[tru_idx]] += delta

            # False Negative -- watch for other terminals
            if seq[-1] not in self.terminals:
                self.other_terminals[seq[-1]] += 1

        if self.min_obs > 1:
            for tok, tokdata in self.terminals.items():
                for ctx, data in tokdata.exceptions.items():
                    #  remove rare exceptions
                    for key, val in list(data.items()):
                        if val < self.min_obs:
                            del data[key]
        if verbose:
            # Print
            from pprint import pprint
            for tok, tokdata in self.terminals.items():
                print("== %s" % tok)
                for ctx, data in tokdata.exceptions.items():
                    print("======== %s===" % ctx)
                    pprint(sorted(data.items(), key=lambda x: x[1], reverse=True))
            print("Other terminals::")
            pprint(self.other_terminals)
            print("Learned from %d records" % count)

    def learn_from(self, lines, verbose=False):
        def prepare():
            for line in lines:
                if self.nocase:
                    line = line.lower()
                line = line.strip()
                if line:
                    yield self.tokenize(line)
        seq = prepare()
        self.learn(seq, verbose=verbose)

    def split(self, long_seq):
        if not seq:
            return seq
        res = []
        left = 0
        for idx in range(1, len(long_seq)):
            if long_seq[idx] in self.terminals:
                do_split = True
                model = self.terminals[long_seq[idx]]
                for rel_ctx_idx, exepts in model.exceptions.items():
                    tru_ctx_idx = rel_ctx_idx + idx
                    if 0 <= tru_ctx_idx < len(long_seq):
                        tok = long_seq[tru_ctx_idx]
                        if self.nocase:
                            tok = tok.lower()
                        if tok in exepts:
                            do_split = False           # its a false pos, dont split
                if do_split:
                    res.append(long_seq[left: idx + 1])
                    left = idx + 1

        if left < len(long_seq):    # left over sequence ending
            res.append(long_seq[left:])
        return res


if __name__ == '__main__':
    import argparse
    import sys
    p = argparse.ArgumentParser()
    p.add_argument('command', nargs=1, help='action command', choices=['learn', 'split'])
    p.add_argument('model', nargs=1, help="model")
    p.add_argument('-in', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    p.add_argument('-out', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    p.add_argument('-ci', action='store_true', help="Case Insensitive")
    p.add_argument('-vv', action='store_true', help="Print stats")
    p.add_argument('-min_obs', default=4, type=int, help="Minimum Observation of exceptions, default=4")

    args = vars(p.parse_args())

    cmd = args['command'][0]
    model = args['model'][0]
    if cmd == 'learn':
        spltr = TerminalSplitter(min_observations=args['min_obs'], nocase=args['ci'])
        spltr.learn_from(args['in'], verbose=args['vv'])
        spltr.save(model)

    elif cmd == 'split':
        spltr = SeqSplitter.load(model)
        for seq in args['in']:
            seq = spltr.tokenize(seq.strip())
            splits = spltr.split(seq)
            for split in splits:
                args['out'].write(spltr.detokenize(split))
                args['out'].write("\n")
            args['out'].write("\n")
    else:
        raise Exception()

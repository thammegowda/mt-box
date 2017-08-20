
import gzip
import codecs
from argparse import ArgumentParser
from fuzzy import nysiis as sound_sig
import sys
from solr import Solr
import logging as log

log.basicConfig(level=log.INFO)


class Sound2Name(object):

    def __init__(self, path, topk=4):
        opener = gzip if path.endswith('.gz') else codecs
        with opener.open(path, 'rb', 'utf-8') as f:
            names = f.readlines()
            self.names = list(map(lambda x: x.strip(), names))

        log.info("Found %d names. Indexing Sounds" % len(self.names))
        self.index = {}

        for name in self.names:
            sig = sound_sig(name)
            if sig not in self.index:
                self.index[sig] = set()
            self.index[sig].add(name)
        log.info("Found %d sounds." % len(self.index))

    def popularity_score(self, name):

        pass


class PhoneticNameMatcher(object):

    def __init__(self, path):
        opener = gzip if path.endswith('.gz') else codecs
        with opener.open(path, 'rb', 'utf-8') as f:
            names = f.readlines()
            self.names = list(map(lambda x: x.strip(), names))

        log.info("Found %d names. Indexing Sounds" % len(self.names))
        self.index = {}

        for name in self.names:
            sig = sound_sig(name)
            if sig not in self.index:
                self.index[sig] = set()
            self.index[sig].add(name)
        log.info("Found %d sounds." % len(self.index))

    def find_matches(self, word):
        sig = sound_sig(word)
        return sig, self.index.get(sig, None)


def interactive(matcher):
    print("Enter location Name:")
    try:
        while True:
            sys.stdout.write('>')
            line = raw_input('>').strip()
            sig, res = matcher.find_matches(line)
            print("Sound Signature:", sig)
            if res:
                res = sorted(list(res))
            print(res)
    except EOFError as e:
        print('Bye!')

if __name__ == '__main2__':
    p = ArgumentParser()
    p.add_argument('-n', '--names', required=True, help='.txt or .txt.gz file having list of names')
    p.add_argument('-i', '--interactive', action='store_true')
    args = vars(p.parse_args())
    matcher = PhoneticNameMatcher(args['names'])
    if args['interactive']:
        interactive(matcher)
    else:
        print('Batch mode not implemented. Use interactive mode')
        sys.exit(1)


if __name__ == '__main__':
    solr = Solr('http://localhost:8983/solr/wiki')
    res = solr.hit_count("\"California\"")
    print(res)

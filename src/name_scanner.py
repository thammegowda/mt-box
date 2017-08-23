#!/usr/bin/env python3

import re
from argparse import ArgumentParser


vowels = set('aeiou')


sounds = {
    'a': 'aeiou',
    'e': 'aeiou',
    'i': 'aeiou',
    'o': 'aeiou',
    'u': 'aeiou',
    'b':'bvp',
    'c': 'cskh',
    'd': 'dg',
    'f': 'pfh',
    'g': 'gdj',
    'h': 'ha',
    'j': 'djz',
    'k': 'ckx',
    'l': 'lh',
    'm': 'mn',
    'n': 'mn',
    'p': 'pfh',
    'q': 'kuxch',
    'r': 'r',
    's': 'scxh',
    't': 'td',
    'v': 'vwb',
    'w': 'vwb',
    'x': 'xsch',
    'y': 'yivu',
    'z': 'zdjh'
}

strict_sounds = {
    'a': 'aeiou',
    'e': 'aeiou',
    'i': 'aeiou',
    'o': 'aeiou',
    'u': 'aeiou',
    'b':'b',
    'c': 'csk',
    'd': 'dg',
    'f': 'pf',
    'g': 'gdj',
    'h': 'h',
    'j': 'j',
    'k': 'ck',
    'l': 'l',
    'm': 'm',
    'n': 'n',
    'p': 'pf',
    'q': 'qku',
    'r': 'r',
    's': 'sc',
    't': 'td',
    'v': 'vw',
    'w': 'vw',
    'x': 'xks',
    'y': 'yi',
    'z': 'zdj'
}



def lookup(items, pattern):
    return (i for i in items if pattern.match(i))


def compile_patterns(names, allow_prefix=False, allow_suffix=True, strict=False):
    table = strict_sounds if strict else sounds
    names = set(names)
    ps = {}
    for name in names:
        p = ['^']
        if allow_prefix:
            p.append('.*')
        for ch in name:
            if ch in table:
                # vowel = 0 or more times, consonants 1 or more times
                freq = '*' if ch in vowels else '+'                     
                p.append('[%s]%s' % (table[ch], freq))
            else:
                print('>>ERROR: Character is unknown %s' % ch)
                p.append('%s*' % ch)
        if allow_suffix:
            p.append('.*')
        p.append('$')
        patrn = ''.join(p)
        ps[name] = re.compile(patrn)
    return ps

def read_file(path):
    with open(path) as f:
       return [line.strip() for line in f]


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-n', help='File having names.', required=True)
    parser.add_argument('-i', help='File having input tokens to scan for names', required=True)
    parser.add_argument('-as', help='Allow Suffixes', action='store_true', default=False)
    parser.add_argument('-ap', help='Allow Prefixes', action='store_true', default=False)
    parser.add_argument('-strict', help='Strict match Sounds only . reduces false possitives', action='store_true', default=False)
    args = vars(parser.parse_args())
    names = read_file(args['n'])
    cands = read_file(args['i'])
    pats = compile_patterns(names, args['ap'], args['as'], args['strict'])
    for k,v in pats.items():        
        res = list(lookup(cands,v))
        if len(res) > 40:
            print(">> %s :: Skipping.. more than 40 matches" % k)
        elif not res:
            print(">> %s :: No matches" % k)
        else:
            print(k, v)
            print(res)
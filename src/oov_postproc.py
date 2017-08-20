from codecs import open as copen
from argparse import ArgumentParser
import fuzzy
import random
import gzip, codecs
import logging as LOG
import sys
from elisa import parse_elisa


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
        with copen(dict_file) as file:
            for line in file:
                parts = line.strip().split("\t")
                if len(parts) != 3:
                    print(">Skip:", line)
                    continue
                p, f, e = parts

                if f not in self.f2e:
                    self.f2e[f] = set()
                count += 1
                self.f2e[f].add(f)
        for k in self.f2e.keys():
            self.f2e[k] = list(self.f2e[k])
        print("> Mappings has %d words to %d english words" % (len(self.f2e), count))

        self.f_sounds = {}
        for f in self.f2e:
            f_sound = self.sound_sig(f)
            if f_sound not in self.f_sounds:
                self.f_sounds[f_sound] = set()
            self.f_sounds[f_sound].add(f)

        for k in self.f_sounds.keys():
            self.f_sounds[k] = list(self.f_sounds[k])

    def sound_sig(self, word):
        """
        Sound signature of word
        :param word:
        :return:
        """
        return fuzzy.nysiis(word)

    def translate_oow(self, word, ctx=None, pos=None):

        if word in self.f2e:
            return random.choice(self.f2e[word])

        # all upper case, like NASA, USA or UNICEF
        if word.isupper() and 2 < len(word) < 6:
            return word

        if word.istitle() and 2 < len(word):
            # is it name of person, location or any NAMED ENTITY
            # Do soundex or NYSII match
            sound_sig = self.sound_sig(word)
            print("Sound %s is %s" % (word, sound_sig))
            if sound_sig in self.f_sounds:
                print("Sound match found")
                # TODO: get closest sounding word, may be edit distance would do
                chosen = random.choice(self.f_sounds[sound_sig])
                # translate to english
                return random.choice(self.f2e[chosen])
        print("> Couldnt translate OOV word: %s", word)
        return word

    def translate_segment(self, seg):
        res = []
        idx = 0
        for tok, tag in seg.get_tokens():
            if tag == 'UNK':
                trans = self.translate_oow(tok, seg, idx)
                res.append(trans)
            else:
                res.append(tok)
            idx += 1
        return res

    def post_process(self, seg):
        seq = self.translate_segment(seg)
        sent = ' '.join(seq)
        # capitalize first alphabet in sentence
        firstchar = 0
        while firstchar < len(sent) and not sent[firstchar].isalpha():
            firstchar += 1
        if firstchar < len(sent):
            sent = sent[:firstchar] + sent[firstchar].upper() + sent[firstchar+1:]

        # remove space between puncts and words
        #sent = re.sub(r'(\w)\s+(\W)', r'\1\2', sent.strip())
        return sent

def sound_sig(word):
    """
    Sound signature of word
    :param word:
    :return:
    """
    return fuzzy.nysiis(word)


class PhoneticNameMatcher(object):

    def __init__(self, path):
        opener = gzip if path.endswith('.gz') else codecs
        with opener.open(path, 'rb') as f:
            names = f.readline()
            self.names = list(map(lambda x: x.strip(), names))

        LOG.info("Found %d names" % len(self.names))
        self.index = {}

        for name in self.names:
            sig = sound_sig(name)
            if sig not in self.index:
                self.index[sig] = set()
            self.index[sig].add(sig)

    def __find_matches__(self, word):
        sig = sound_sig(word)
        return self.index.get(sig, None)

if __name__ == '__main__':
    parser = ArgumentParser(description='Out of Vocabulary Post Processor (for ELISA)')
    parser.add_argument('-i', '--in', help='ELISA XML file', required=True)
    parser.add_argument('-o', '--out', help='OUTPUT FILE', required=True)
    parser.add_argument('-gl', '--geo-list', help='List of geo names in english', required=True)

    args = vars(parser.parse_args())
    oov_trans = OOVTranslator(args['dict'])

    segs = parse_elisa(args['in'])
    sents = map(oov_trans.post_process, segs)
    dump_stream(sents, args['out'])

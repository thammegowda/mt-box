from codecs import open as copen
from lxml import etree as ET


class Segment(object):
    """
    Segment data structure
    """
    def __init__(self, src_id, tgt_id, src, tgt_tokens, tgt_tags):
        assert src and tgt_tokens and tgt_tags
        assert len(tgt_tokens) == len(tgt_tags)
        self.src = src
        self.tgt_tokens = tgt_tokens
        self.tgt_tags = tgt_tags
        self.src_id = src_id
        self.tgt_id = tgt_id

    def get_tokens(self):
        return zip(self.tgt_tokens, self.tgt_tags)

    def __repr__(self):
        tags = ' '.join(map(lambda x: '%s/%s' % (x[0], x[1]), zip(self.tgt_tokens, self.tgt_tags)))
        return '''Segment(...%s ...%s, %s --> %s''' % \
               (self.src_id[-4:], self.tgt_id[-4:], self.src, tags)


TAG_MAP = {'unknown': 'UNK', 'translation': 'T', 'identity': 'IDEN'}
def tag_mapper(tag):
    return TAG_MAP.get(tag, tag)


def parse_elisa(path):
    """
    Parse elisa package
    :param path:
    :return:
    """
    tree = ET.parse(path)
    for seg_el in tree.xpath('//SEGMENT'):
        src_id = seg_el.xpath('.//SOURCE/@id')[0]
        tgt_id = seg_el.xpath('.//TARGET/@id')[0]
        src = seg_el.xpath('.//ULF_LRLP_TOKENIZED_SOURCE/text()')[0]
        tok_els = seg_el.findall('.//TOKENIZED_TARGET/TOKEN')
        tokens = [tok.text for tok in tok_els]

        tags = [tag_mapper(tok.attrib['rule-class']) for tok in tok_els]
        yield Segment(src_id, tgt_id, src, tokens, tags)


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

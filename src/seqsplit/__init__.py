
from abc import abstractmethod, ABC
import pickle
import logging as log

__author__ = 'Thamme Gowda'
__created__ = 'November 29, 2017'
__version__ = '0.1'
log.basicConfig(level=log.INFO)


class SeqSplitter(ABC):

    @abstractmethod
    def learn(self, seqs):
        pass

    @abstractmethod
    def split(self, raw_seq):
        pass

    def tokenize(self, seq):
        return seq.split()

    def detokenize(self, seq):
        return ' '.join(seq)

    def save(self, path):
        log.info("Saving the model %s at %s" % (type(self), path))
        pickle.dump(self, open(path, 'wb'))

    @staticmethod
    def load(path):
        log.info("Loading model from %s " % path)
        with open(path, 'rb') as f:
            self = pickle.load(f)
            assert isinstance(self, SeqSplitter)
            return self

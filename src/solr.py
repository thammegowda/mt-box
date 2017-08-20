
import requests

#from functools32.functools32 import lru_cache
from functools import lru_cache
import logging as log


class Solr(object):

    def __init__(self, url, field='titleText'):
        self.url = url + "/select"
        self.field = field

    @lru_cache(int(1e6))
    def hit_count(self, phrase, **kwargs):
        payload = {
            'q': '%s:%s' % (self.field, phrase),
            'wt': 'python',
            'rows': 0
        }
        if kwargs:
            for key in kwargs:
                payload[key] = kwargs.get(key)
        #print("Query", payload)
        resp = requests.get(self.url, params=payload)
        if resp.status_code == 200:
            result = eval(resp.text)
            return result['response']['numFound']
        else:
            log.error("Solr Response Code = %d" % resp.status_code)
            log.error("Payload was %s" % payload)
            return None

    def get_top(self, query, rows=1, **kwargs):
        payload = {
            'q': query,
            'wt': 'python',
            'rows': rows
        }
        if kwargs:
            for key in kwargs:
                payload[key] = kwargs.get(key)
        #print("Query", payload)
        resp = requests.get(self.url, params=payload)
        if resp.status_code == 200:
            return eval(resp.text)['response']
        else:
            log.error("Solr Response Code = %d" % resp.status_code)
            log.error("Payload was %s" % payload)
            return None
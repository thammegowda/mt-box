"""
Custom Data Structures

1. Trie - for prefix matching
"""

import logging as log
from collections import defaultdict
from pprint import pprint

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

    def bfs_nodes(self):
        que = [self]
        while que:
            node = que.pop(0)
            yield node
            que.extend(node.kids.values())

    def bfs_edges(self):
        que = [(None, self)]
        while que:
            par, kid = que.pop(0)
            if par is not None:
                yield (par, kid)
            que.extend(map(lambda x: (kid, x), kid.kids.values()))

    def path(self, seq):
        nodes = []
        node = self
        for c in seq:
            if c in node.kids:
                node = node.kids[c]
                nodes.append(node)
            else:
                break
        return nodes, seq[len(nodes):]

    def terminal_children(self):
        if self.is_term:
            yield self
        for k in self.kids.values():
            yield from k.terminal_children()

    def __repr__(self):
        return self.get_path() + ('*' if self.is_term else '')

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.get_path())

    def __eq__(self, other):
        return isinstance(other, Trie) and self.get_path() == other.get_path()

    def __len__(self):
        return self.count

    @staticmethod
    def build(words):
        root = Trie('/', None)
        for word in words:
            if word is not None:
                root.add_word(word)
        return root


class DAG(object):

    class Node(object):

        def __init__(self, uid, name=None, **kwargs):
            assert uid is not None
            self.uid = uid
            self.name = name if name else self.uid
            # store links to Nodes
            self.ins = {}
            self.outs = {}
            self.data = kwargs

        def __str__(self):
            return self.name

    class Edge(object):

        def __init__(self, start, end, uid=None, name=None, **kwargs):
            self.start = start
            self.end = end
            self.uid = uid if uid else DAG.Edge.make_uid(start, end)
            self.name = name if name else '%s-%s' % (start.name, end.name)
            self.data = kwargs

        def __str__(self):
            return self.name

        def update_sig(self):
            self.uid = DAG.Edge.make_uid(self.start, self.end)
            self.name = '%s-%s' % (self.start.name, self.end.name)

        @staticmethod
        def make_uid(node1, node2):
            return "%s-%s" % (node1.uid, node2.uid)

    def __init__(self, name=""):
        self.name = name
        self.node_idx = {}
        self.edge_idx = {}

    def add_nodes(self, nodes):
        for node in nodes:
            self.add_node(node)

    def add_node(self, node):
        # print(node, type(node), isinstance(node, self.Node))
        assert isinstance(node, self.Node)
        assert node.uid not in self.node_idx
        self.node_idx[node.uid] = node

    def connect(self, start, end):
        if type(start) is str and start in self.node_idx:
            start = self.node_idx[start]
        if type(end) is str and end in self.node_idx:
            end = self.node_idx[end]
        assert isinstance(start, self.Node), '%s is not a known Node ' % start
        assert isinstance(end, self.Node), '%s is not a known Node' % end
        if start.uid not in self.node_idx or end.uid not in self.node_idx:
            log.error("Cant connect %s -> %s " % (start.uid, end.uid))
        assert start.uid in self.node_idx
        assert end.uid in self.node_idx
        edge = self.Edge(start, end)
        self.add_edge(edge)
        return edge

    def connect_all(self, pairs):
        for start, end in pairs:
            self.connect(start, end)

    def add_edges(self, edges):
        for edge in edges:
            self.add_edge(edge)

    def add_edge(self, edge):
        assert isinstance(edge, self.Edge)
        edge.start.outs[edge.name] = edge
        edge.end.ins[edge.name] = edge
        self.edge_idx[edge.uid] = edge

    def get_node(self, uid):
        return self.node_idx[uid]

    def get_nodes(self):
        return self.node_idx.values()

    def get_edge(self, uid):
        return self.edge_idx[uid]

    def get_edges(self):
        return self.edge_idx.values()

    def merge_nodes(self, node1, node2):
        """
        Merges two nodes and returns a resulting merged node.
        The default implementation simply copies second node to first, removes the second, and returns the first arg
        :param node1: first node
        :param node2: second node
        :return: merged node
        """
        new_node = node1
        # update incoming edges of node2
        # update outgoing edges of node2
        # copy data from node2 to node1
        # remove node 2
        # update edge UIDs, since edge uids are derived from node uids
        edge_updates = {}
        edge_removals = set()
        for edge, prev_node in node2.ins.items():
            edge.end = new_node
            prev_node.outs[edge] = new_node
            new_node.ins[edge] = prev_node
            edge_removals.add(edge.uid)
            edge.update_sig()
            edge_updates[edge.uid] = edge

        for edge, nxt_node in node2.outs.items():
            edge.start = new_node
            nxt_node.ins[edge] = new_node
            new_node.outs[edge] = nxt_node
            edge_removals.add(edge.uid)     # remove current ID
            edge.update_sig()
            edge_updates[edge.uid] = edge

        # TODO: proper merge of data
        node1.data['merged_%s' % node2.uid] = node2.data
        if node2.uid in self.node_idx:
            log.info("Delete node %s" % node2.uid)
            del self.node_idx[node2.uid]
        # edges UID index is to be updated because uid = <node1>-<node2>
        for e_uid in edge_removals:
            if e_uid in self.edge_idx:
                log.info("Delete EDGE %s" % e_uid)
                del self.edge_idx[e_uid]
        self.edge_idx.update(edge_updates)
        return new_node

    def to_networkx(self):
        import networkx as nx
        DG = nx.DiGraph()
        DG.add_nodes_from(self.get_nodes())
        DG.add_edges_from((e.start, e.end) for e in self.get_edges())
        return DG


class MorphGraph(DAG):

    def __init__(self, words, name="", start="^", end="$"):
        assert type(words) in (list, set)
        super(MorphGraph, self).__init__(name)
        self.name = name
        self.start = start
        self.end = end
        self.words = words
        self.prf_trie = Trie.build(words)
        self.suf_trie = Trie.build(w[::-1] for w in words)
        self.G = self.__merge()

    def __merge(self):
        start_node = self.Node(self.start)
        end_node = self.Node(self.end)
        self.add_nodes((start_node, end_node))

        prf_map = {}
        prf_map_rev = defaultdict(set)
        suf_map = {}
        suf_map_rev = defaultdict(set)
        edges = set()
        merged_nodes = {}
        for w in self.words:
            prf_path, pcut = self.prf_trie.path(w)
            suf_path, scut = self.suf_trie.path(w[::-1])
            assert pcut == scut == ''
            # print("==%s==" % w)
            prev_node = start_node
            assert len(prf_path) == len(suf_path) == len(w)
            for pn, sn, ch in zip(prf_path, suf_path[::-1], w):
                # print(ch, pn.get_path(), sn.get_path())
                # case 1: no mapping exists => new node
                if pn not in prf_map and sn not in suf_map:
                    cur_node = self.Node(uid=pn.get_path(), name=ch)
                    self.add_node(cur_node)
                    prf_map[pn] = cur_node
                    prf_map_rev[cur_node].add(pn)
                    suf_map[sn] = cur_node
                    suf_map_rev[cur_node].add(sn)

                # case 2: One mapping exists
                # case 2a: prefix mapping exists
                elif pn in prf_map and sn not in suf_map:
                    cur_node = prf_map[pn]
                    suf_map[sn] = cur_node
                    suf_map_rev[cur_node].add(sn)

                # case 2b: suffix mapping exists
                elif pn not in prf_map and sn in suf_map:
                    assert sn in suf_map
                    cur_node = suf_map[sn]
                    prf_map[pn] = cur_node
                    prf_map_rev[cur_node].add(pn)

                # case 3: Both mapping exists
                elif pn in prf_map and sn in suf_map:
                    #  - case 3a: both mapped to same node
                    if prf_map[pn] == suf_map[sn]:
                        cur_node = prf_map[pn]
                    # - case 3b: both are mapped to different node in merged graph --> merge them
                    else:
                        """this is a bit complex merge operation. Its done like this
                        Eg words: ['XLONES', 'XMPERE', 'XMPERES'] 
                        When these are processed in the same order,
                        the 'E' in XLONES and last 'E' in XMPERES are mapped to two different nodes in the merged graph
                        based on prefix and suffix tries respectively.
                        So we are going to merge both the 'E' nodes to same, to make single 'ES' suffix
                        1. First we ask the DAG graph to merge those nodes (it should update edges its internal structures
                        2. prf_map and suf_map has projects, we ask them to update to the new merged node.
                            a) this is done quickly by constructing the prf_map_rev and suf_map_rev index ahead of the time.
                        3. point the cur_node to merged node
                        4. update prf_map suf_map for the current pn and sn
                        5. update the reverse maps of cur_node
                        TODO: Maybe there is a simpler way to accomplish the same task  
                        """
                        log.info("Merging -- %s at %s" % (w, ch))
                        node1 = prf_map[pn]
                        node2 = suf_map[sn]
                        new_node = self.merge_nodes(node1, node2)
                        for old_node in (node1, node2):
                            # prefix - update projection mappings
                            for prf_proj_node in prf_map_rev[old_node]:
                                prf_map[prf_proj_node] = new_node
                            # suffix - update projection mappings
                            for suf_proj_node in suf_map_rev[old_node]:
                                suf_map[suf_proj_node] = new_node
                        cur_node = new_node
                        prf_map[pn] = suf_map[sn] = cur_node   # this may have been done already in the above loop
                        prf_map_rev[cur_node] = prf_map_rev[node1] | prf_map_rev[node2] | {pn, sn}
                        if node1.uid != cur_node.uid:
                            merged_nodes[node1.uid] = cur_node.uid
                        if node2.uid != cur_node.uid:
                            merged_nodes[node2.uid] = cur_node.uid
                else:
                    print(pn in prf_map, sn in suf_map)
                    raise Exception('Shouldnt happen! - Case not handled')

                # save edges to add later
                edges.add((prev_node.uid, cur_node.uid))
                prev_node = cur_node
            edges.add((prev_node.uid, end_node.uid))

        print("%d edges " % len(edges))
        # self.connect_all(edges)

        def update_edge(pair):
            print(pair, end='-->')
            start, end = pair
            assert type(start) == str and type(end) == str
            # update signature of edges
            if start in merged_nodes:
                start = merged_nodes[start]
            if end in merged_nodes:
                end = merged_nodes[end]
            print((start, end))
            return start, end
        # resolve transitive merge A->B, B->C ==> A->C
        for old, new in list(merged_nodes.items()):
            while new in merged_nodes:
                new = merged_nodes[new]
            merged_nodes[old] = new
        # Update mappings of edges, update signatures, drop duplicates
        for key, val in merged_nodes.items():
            print("MERGE: %s -> %s" % (key, val))
        edges = set(map(update_edge, edges))
        print("%d edges " % len(edges))
        self.connect_all(edges)


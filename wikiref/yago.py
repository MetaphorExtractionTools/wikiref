# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import pickle
import leveldb


from wikiref.semadata import SemanticNodeSet
from wikiref.settings import LDB_ARRAY_DELIM


class YagoClassDict(object):
    """
    Maps: <yago_label> -> [<yago_node>]
    """

    def __init__(self, data_root):
        self.data_root = data_root
        self.ldb = leveldb.LevelDB(data_root)

    def get(self, term, default=None):
        try:
            return SemanticNodeSet(lemmas=[term], nodes=self.ldb.Get(term).split(LDB_ARRAY_DELIM))
        except KeyError:
            return default

    def __getitem__(self, key):
        return self.get(key)

    def __repr__(self):
        return "<YagoDict(data=%s)>" % self.data_root


class YagoClassSearch(object):
    """
    Map: <word> -> [<yago_node>]
    """

    def __init__(self, data_root):
        self.data_root = data_root
        self.ldb = leveldb.LevelDB(data_root)

    def get(self, lemma_or_lemmas, default=None):
        if isinstance(lemma_or_lemmas, list) or isinstance(lemma_or_lemmas, tuple):
            return self.search(lemma_or_lemmas, default=default)
        else:
            return self.search([lemma_or_lemmas], default=default)

    def search(self, lemmas, default=None):
        node_sets = []
        for lemma in lemmas:
            try:
                lemma_nodes = self.ldb.Get(lemma).split(LDB_ARRAY_DELIM)
            except KeyError:
                return default
            node_sets.append(lemma_nodes)
        conjunction = set(node_sets[0])
        for i in xrange(1, len(node_sets)):
            node_set = node_sets[i]
            conjunction.intersection_update(node_set)
        if len(conjunction) == 0:
            return default
        return SemanticNodeSet(lemmas=lemmas, nodes=conjunction)

    def __getitem__(self, key):
        return self.get(key)

    def __repr__(self):
        return "<YagoSearchDict(data=%s)>" % self.data_root


class YagoTaxonomy(object):
    """
    Map: <child_node> -> [<parent_node>]
    """

    def __init__(self, data_root):
        self.data_root = data_root
        self.ldb = leveldb.LevelDB(data_root)

    def get_parent(self, node, default=None):
        try:
            if isinstance(node, list):
                node = node
            value = self.ldb.Get(node).split(LDB_ARRAY_DELIM)[0]
            return value
        except KeyError:
            return default

    def __getitem__(self, key):
        return self.get_parent(key)

    def __repr__(self):
        return "<YagoTaxonomyDict(data=%s)>" % self.data_root


class YagoTypes(object):

    def __init__(self, data_root):
        self.data_root = data_root
        self.ldb = leveldb.LevelDB(data_root)

    def get_parent(self, node, default=[]):
        try:
            return self.ldb.Get(node).split(LDB_ARRAY_DELIM)
        except KeyError:
            return default

    def __getitem__(self, key):
        return self.get_parent(key)

    def __repr__(self):
        return "<YagoTransitiveDict(data=%s)>" % self.data_root


# class YagoPreferredSearch(object):

#     def __init__(self, data_root):
#         self.data_root = data_root
#         self.ldb = leveldb.LevelDB(data_root)

#     def get(self, lemma_or_lemmas, default=None):
#         if isinstance(lemma_or_lemmas, list) or isinstance(lemma_or_lemmas, tuple):
#             return self.search(lemma_or_lemmas, default=default)
#         else:
#             return self.search([lemma_or_lemmas], default=default)

#     def search(self, lemmas, default=None):
#         node_sets = []
#         for lemma in lemmas:
#             try:
#                 lemma_nodes = set(self.ldb.Get(lemma).split(DELIM))
#             except KeyError:
#                 return default
#             node_sets.append(lemma_nodes)
#         conjunction = node_sets[0]
#         for i in xrange(1, len(node_sets)):
#             node_set = node_sets[i]
#             conjunction.intersection_update(node_set)
#         if len(conjunction) == 0:
#             return default
#         return SemanticNodeSet(lemmas=lemmas, nodes=conjunction)

#     def __getitem__(self, key):
#         return self.get(key)

#     def __repr__(self):
#         return "<YagoSearchDict(data=%s)>" % self.data_root
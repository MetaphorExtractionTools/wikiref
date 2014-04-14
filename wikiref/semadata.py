# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import re
import os
import pickle
import leveldb
import logging
import sqlite3
import itertools
import StringIO as stringio


DEAFULT_SET = {
    "<wordnet_person_100007846>",
    "<wordnet_person_105217688>"
}


ARG_NONE = 0x0
ARG_EMPTY = 0x1


class NodeType(object):
    WORDNET         = 0x01
    OWL             = 0x02
    WIKI_INSTANCE   = 0x03
    WIKI_CATEGORY   = 0x04
    YAGO            = 0x05


class ConceptRelation(object):
    RELATED         = 0x01
    DERIVED         = 0x02
    SYNONYM         = 0x03


class SemanticTerm(object):
    word_re = re.compile("\b[^\W\d_]+\b")

    def __init__(self, node, label):
        self.node = node
        self.label = label

    @staticmethod
    def instance_size(inst_node):
        return len(SemanticTerm.word_re.findall(inst_node))


    @staticmethod
    def extract_transition(tsv_line):
        line = tsv_line.decode("utf-8")
        row = line.split("\t")
        return row[1], row[3]

    def __repr__(self):
        repr_str = "<SemanticTerm(label='%s', class=%s)>" % (self.label, self.node)
        return repr_str.encode("utf-8")


class SemanticNodeSet(object):

    def __init__(self, lemmas, nodes):
        self.lemmas = lemmas
        self.nodes = [n for n in nodes if n != "owl:Thing"]

    @staticmethod
    def is_instance(node):
        if node.startswith("<wordnet_"):
            return False
        if node.startswith("owl:"):
            return False
        if node.startswith("<yago"):
            return False
        if node.startswith("<wikicategory"):
            return False
        return True

    @staticmethod
    def is_wclass(node):
        # if node.startswith("<wordnet"):
        #     return True
        # return False
        return not SemanticNodeSet.is_instance(node)

    @staticmethod
    def is_wclass_or_instance(node):
        if node.startswith("owl:"):
            return False
        if node.startswith("<yago"):
            return False
        if node.startswith("<wikicategory"):
            return False
        return True

    def __repr__(self):
        return "<SemanticNodeSet(lemmas=[%s], instances=%d, classes=%d, nodes=[%s])>" % (
            " ".join(self.lemmas),
            self.instance_count(),
            self.class_count(),
            ", ".join(self.nodes),
        )

    def instances(self):
        return filter(self.is_instance, self.nodes)

    def wclasses(self):
        return filter(self.is_wclass, self.nodes)

    def pretty(self):
        string = stringio.StringIO()
        string.write("\nSemanticNodeSet:\n\n")
        utf8_lemmas = map(lambda s: s.decode("utf-8"), self.lemmas)
        string.write("lemmas: [%s] \n\n" % " ".join(utf8_lemmas))
        for node in self.nodes:
            string.write("\t + node: %s\n" % node)
        string.write("\n")
        return string.getvalue()

    def as_wclasses(self):
        return SemanticNodeSet(self.lemmas, filter(self.is_class, self.nodes))

    def as_instances():
        return SemanticNodeSet(self.lemmas, filter(self.is_instance, self.nodes))

    def classes_len(self):
        return len(filter(self.is_class, self.nodes))

    def generalize(self, types, taxonomy, levels=1):
        instance_nodes = set()
        for node in self.nodes:
            if self.is_instance(node):
                instance_nodes.update(types[node])
        if levels > 1 or len(filter(self.is_wclass, instance_nodes)) == 0:
            if levels == 1:
                levels += 1
            prev_classes = instance_nodes

            while levels > 1 and len(prev_classes) > 0:
                new_classes = []
                for node in prev_classes:
                    parent = taxonomy[node]
                    if parent is not None:
                        new_classes.append(parent)

                instance_nodes.update(new_classes)
                prev_classes = new_classes

                for cl in prev_classes:
                    if self.is_wclass(cl):
                        levels -= 1
                        break

        # print list(filter(self.is_wclass, instance_nodes))
        return SemanticNodeSet(self.lemmas, filter(self.is_wclass, instance_nodes))

    def class_count(self):
        return len(filter(self.is_wclass, self.nodes))

    def instance_count(self):
        return len(filter(self.is_instance, self.nodes))

    def size(self):
        return  len(self.nodes)

    def isempty(self, yago_types):
        if len(self.nodes) == 0:
            return True
        if self.class_count() == 0 and self.instance_count() > 0:
            for instance in filter(self.is_instance, self.nodes):
                if len(yago_types[instance]):
                    return False
            return True
        return False

    def __len__(self):
        return self.size()

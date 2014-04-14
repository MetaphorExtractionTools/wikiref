# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import gc
import re
import os
import lz4
import random
import logging
import leveldb
import StringIO
import itertools

from wikiref.settings import MERGING_INDEX_TRIPLE_ID_DELIMITER
from wikiref.settings import MERGING_INDEX_TRIPLE_LINE_DELIMITER


WN_RE = re.compile("^<\w+_(.+)_\d+>$")
VISITED = set()


class MergeIndex(object):
    MAX_CACHE_SIZE = 4096 * 256

    def __init__(self, odir):
        db_dir = os.path.join(odir, "merge_index")
        self.leveldb = leveldb.LevelDB(db_dir)
        self.cache = {}
        self.cache_size = 0

    def add_triple_line(self, triple_id, triple_str, triple_pattern):
        if triple_pattern in self.cache:
            self.cache[triple_pattern].append((str(triple_id), triple_str))
        else:
            self.cache[triple_pattern] = [(str(triple_id), triple_str)]
        self.cache_size += 1
        if self.cache_size > self.MAX_CACHE_SIZE:
            self.dump_cache()

    def dump_cache(self):
        batch = leveldb.WriteBatch()
        for pattern, triple_id_pairs in self.cache.iteritems():
            try:
                pattern_triples = self.leveldb.Get(pattern)
                pattern_triples = lz4.decompress(pattern_triples)
                pattern_triples = pattern_triples.split(MERGING_INDEX_TRIPLE_LINE_DELIMITER)
            except KeyError:
                pattern_triples = []
            logging.info("Merging bin from %d to %d (%d new)." % (
                len(pattern_triples),
                len(pattern_triples) + len(triple_id_pairs),
                len(triple_id_pairs),
            ))
            for triple_id_pair in triple_id_pairs:
                pattern_triples.append(MERGING_INDEX_TRIPLE_ID_DELIMITER.join(triple_id_pair))
            pattern_triples_dump = MERGING_INDEX_TRIPLE_LINE_DELIMITER.join(pattern_triples)
            batch.Put(pattern, lz4.compressHC(pattern_triples_dump))
        self.leveldb.Write(batch)
        logging.info("Dump %d bins." % len(self.cache))
        self.cache = {}
        self.cache_size = 0
        gc.collect()

    def get_bin(self, pattern):
        pattern_triples = self.leveldb.Get(pattern)
        pattern_triples = lz4.decompress(pattern_triples)
        pattern_triples = pattern_triples.split(MERGING_INDEX_TRIPLE_LINE_DELIMITER)
        triple_id_pairs = [line.split(MERGING_INDEX_TRIPLE_ID_DELIMITER) for line in pattern_triples]
        return {tr_id: tr_line for tr_id, tr_line in triple_id_pairs}


def get_pattern(triple):
    pattern = StringIO.StringIO()
    pattern.write(triple.rel_type)
    nn_count = 0
    for arg in triple.arguments:
        if arg is not None:
            term = arg[0]
            pos = arg[1]
            if not pos.startswith("NN"):
                pattern.write("_")
                pattern.write(term)
            else:
                pattern.write("_NN")
                nn_count += 1
        else:
            pattern.write("_*")
    if nn_count == 0:
        return None
    # if nn_count > 1:
    #     logging.info(triple)
    #     logging.info(pattern.getvalue())
    #     exit(0)
    return pattern.getvalue()


def wn_name(node):
    return WN_RE.findall(node)[0]


def decode_triple(triple, lemma_dict, wnode_dict):
    triple_id, triple_args = triple
    tr_str = StringIO.StringIO()
    tr_str.write("<id=%r " % triple_id)
    for lemma_id, nodes_id in triple_args:
        tr_str.write("\t%s {%s}" % (
            lemma_dict[lemma_id],
            ",".join([wn_name(wnode_dict[nid]) for nid in nodes_id])
            )
        )
    tr_str.write(">")
    return tr_str.getvalue()


def extract_nodes(args):
    arg_1, = args
    lemma_id, nodes = arg_1
    return nodes


def just_nodes(triples):
    for triple_id, args in triples:
        yield triple_id, extract_nodes(args)


def just_lemmas(triples, lemma_dict):
    lemmas = {}
    for triple_id, args in triples:
        arg_1, = args
        lemma_id, nodes = arg_1
        lemmas[triple_id] = lemma_dict[lemma_id]
    return lemmas

def intersect(*d):
    sets = iter(map(set, d))
    result = sets.next()
    for s in sets:
        result = result.intersection(s)
    return result


def preproc(triples):
    tr_dict = {}
    for t_id, t_args in triples:
        if t_args not in tr_dict:
            tr_dict[t_args] = [t_id]
        else:
            tr_dict[t_args].append(t_id)
    for args, ids in tr_dict.iteritems():
        yield (tuple(ids), args)

def get_lemmas(lemmas, i_idx, nodes):
    triples = intersect(*[tuple(i_idx[nid]) for nid in nodes])
    # print triples
    lemmas_strs = set([lemmas[tr_id] for tr_id in triples])
    if len(lemmas_strs) >= 2:
        return "{%s}" % ", ".join(lemmas_strs)
    else:
        return None

def pruned_search(idx):

    idx2 = {(t,): nodes for t, nodes in idx.iteritems()}
    triples = idx2.keys()[:]
    level_dict = {1: [triples[0]]}
    max_level = 1

    for t1 in triples[1:]:
        level = max_level

        while level > 0:

            level_triples = level_dict.get(level)[:]
            level_dict[1].append(t1)

            for t2 in level_triples:

                nodes_1 = idx2[t1]
                nodes_2 = idx2[t2]
                intr = intersect(nodes_1, nodes_2)

                if len(intr) > 0:

                    new_triple = tuple(set(t1 + t2))
                    new_nodes = tuple(intr)
                    new_level = level + 1

                    idx2[new_triple] = new_nodes

                    if new_level in level_dict:
                        level_dict[new_level].append(new_triple)
                    else:
                        level_dict[new_level] = [new_triple]

                    if max_level < new_level < 3:
                        max_level = new_level
                        level = 0

            level -= 1

    return 0, set([tuple(sorted(nodes)) for nodes in idx2.values()])


def brute_force_search(node_sets, max_comb_size=2):
    """
    Finds all overlapings of given sets. Node sets variable is a list of iterables of integers.
    For example [(1,2,3), (1,2), (2,3,4)]
    Returns list of all found overlaps of node sets: [(1,2), (2), (2,3)]
    """
    new_combs = set()
    comb_sizes = range(min(len(node_sets), max_comb_size), 1, -1)
    for comb_size in comb_sizes:
        combinations = itertools.combinations(node_sets, comb_size)
        for comb in combinations:
            result = tuple(intersect(*comb))
            if len(result) > 0:
                new_combs.add(result)
    return new_combs


def find_overlaps(triples, max_sets_number=3000, passes=5):
    """
    Finds all possible overlaps of triples.
    Triples is list of:
        (triple_id, [
                (lemma_id, [node_1, node_2, ..]),
                (lemma_id, [node_1, node_2, ..]),
                (lemma_id, [node_1, node_2, ..]),
            ]
        )
    Output format: [overlap_1, overlap_2, ...]
    Every overlap is just set of triple ids: overlap=(triple_id_1, triple_id_2, triple_id_3, ..)
    """

    if len(triples) == 0:
        return []

    nn_arity = len(triples[0][1]) # get number of NN arguments
    # Here we will store all overlaps for every argument position,
    # we will later intersect all overlaps in all positions to find the ones,
    # which appear on every position.
    overlaps = []

    # For each NN argument in triples
    for nn_arg_i in xrange(nn_arity):

        tr_node_index = {}  # mapping: triple -> nodes
        node_tr_index = {}  # mapping: nodes -> triple

        for tr_id, args in triples:

            nn_arg = args[nn_arg_i]  # triple's # i'th argument
            _, arg_nodes = nn_arg    # get argument nodes

            # Put them to triple_id -> nodes index
            tr_node_index[tr_id] = set(arg_nodes)

            # put them also to node -> triples index
            for node_id in arg_nodes:
                if node_id in node_tr_index:
                    node_tr_index[node_id].add(tr_id)
                else:
                    node_tr_index[node_id] = {tr_id}

        # Convert sets to hashable tuples
        for k, v in tr_node_index.iteritems():
            tr_node_index[k] = tuple(v)
        for k, v in node_tr_index.iteritems():
            node_tr_index[k] = tuple(v)

        # Get list of all node sets
        all_node_sets = tr_node_index.values()

        # If their number is OK, then find overlaps
        if len(tr_node_index) <= max_sets_number:
            node_sets = all_node_sets
            found_overlaps = brute_force_search(node_sets)

            # Now we have generated node sets overlaps in the following format:
            # found_overlaps := [overlap, overlap, overlap]
            # where each overlap is just set nodes:
            # overlap := [node_1, node_2, node_3, ...]

            # For each overlap, find all triples "participating" in this overlap
            # using inverted `node -> triples` index:
            # Turn list [node_1, node_2, ...] into set: {triples such that have all these nodes on i'th position}.

            # Step 1.
            # [overlap, overlap, overlap] =>
            # [ ([triple, triple, ...], [triple, triple, ], ...), ([..], [..], ...), (..), ...]
            list_of_inverted_nodesets = []
            for overlap in found_overlaps:
                inverted_nodeset = [node_tr_index[node_id] for node_id in overlap]
                list_of_inverted_nodesets.append(inverted_nodeset)

            # Step 2.
            # For each inverted nodeset, intersected its triple lists, so get
            # only triples, which appears has all node.
            intrsected_node_sets = []
            for inverted_nodeset in list_of_inverted_nodesets:
                intersection = intersect(*inverted_nodeset)
                # To make equivalente intersection hash identical, we will sort them
                intersection = tuple(sorted(intersection))
                intrsected_node_sets.append(intersection)

            # Step 3. To remove duplicates, put all triple sets into `set` object.
            overlapping_triples = set(intrsected_node_sets)

        else:
            # otherwise, if their number is too big, get random subset of `max_sets_number` size
            overlapping_triples = set()
            for _ in xrange(passes):
                node_sets =  random.sample(all_node_sets, max_sets_number)
                found_overlaps = brute_force_search(node_sets)

            list_of_inverted_nodesets = []
            for overlap in found_overlaps:
                inverted_nodeset = [node_tr_index[node_id] for node_id in overlap]
                list_of_inverted_nodesets.append(inverted_nodeset)
            intrsected_node_sets = []
            for inverted_nodeset in list_of_inverted_nodesets:
                intersection = intersect(*inverted_nodeset)
                # To make equivalente intersection hash identical, we will sort them
                intersection = tuple(sorted(intersection))
                intrsected_node_sets.append(intersection)
            new_overlapping_triples = set(intrsected_node_sets)

            overlapping_triples |= new_overlapping_triples

        overlaps.append(overlapping_triples)

    nn_arrity_overlaps = sorted(intersect(*overlaps))

    # if nn_arity > 2 and len(nn_arrity_overlaps) > 0:
    #     print "T", triples
    #     print "O", overlaps
    #     print "N", nn_arrity_overlaps
    #     exit(0)


    # __triples_ids = [t[0] for t in triples]

    # if len(triples) < 100 and len(nn_arrity_overlaps) > 0 and nn_arity > 1:
    # if 30667 in __triples_ids:

    return nn_arrity_overlaps


# def find_overlaps(node_sets):

#     # triples = list(just_nodes(triples))
#     # idx = {t_id: nodes for t_id, nodes in triples}

#     # i_idx = {}
#     # for t_id, nodes in triples:
#     #     for nid in nodes:
#     #         if nid not in i_idx:
#     #             i_idx[nid] = [t_id]
#     #         else:
#     #             i_idx[nid].append(t_id)

#     # total, new_combs = pruned_search(idx)

#     total, new_combs = brute_force_search(idx, [t[0] for t in triples])


#     overlaps =

#     return sorted(list(overlaps))


def merge_triples(overlap, bin_triples, str_to_triple):

    new_triple = str_to_triple(bin_triples[overlap[0]])

    # print bin_triples[overlap[0]]
    # print overlap[0]

    # triples = [str_to_triple(bin_triples[triple_id]) for triple_id in overlap]

    # agrnumbers = set([len(t.arguments) for t in triples])
    # logging.info(agrnumbers)

    # if 1 in agrnumbers:
    #     for t in triples:
    #         logging.info(t)
    #     exit(0)


    for triple_id in overlap[1:]:
        combine_triples(new_triple, str_to_triple(bin_triples[triple_id]))

    # print
    # print
    # print "\nTR:".join([bin_triples[o] for o in overlap])
    # print
    # print

    # print overlap

    # print new_triple

    # exit(0)

    # return new_triple

    nn_count = 0


    for arg in new_triple.arguments:
        if arg is None:
            continue
        pos = arg[1]
        if pos.startswith("NN"):
            nn_count += 1

    # logging.info(nn_count)

    if nn_count >= 1:
        for tr_id in overlap:
            print "\t+", tr_id, str_to_triple(bin_triples[tr_id])

        print "=>", new_triple

        print
        print
        print
    #     # exit(0)
    return None
    return new_triple


def combine_triples(tr_1, tr_2):
    for i in xrange(len(tr_1.arguments)):
        arg_1 = tr_1.arguments[i]
        arg_2 = tr_2.arguments[i]
        if arg_1 is None or arg_2 is None:
            continue

        terms_1, pos, nodes_1 = arg_1
        terms_2, pos, nodes_2 = arg_2
        if not pos.startswith("NN"):
            continue

        terms_1 = set(terms_1.split("||"))
        terms_2 = set(terms_2.split("||"))

        new_terms = terms_1 | terms_2

        nodes_1 = set([(n, 1.0) for n, s in nodes_1])
        nodes_2 = set([(n, 1.0) for n, s in nodes_2])

        new_nodes = nodes_1 & nodes_2

        tr_1.arguments[i] = ("||".join(new_terms), pos, new_nodes)

    tr_1.frequency += tr_2.frequency
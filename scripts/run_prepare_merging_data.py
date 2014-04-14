#!/usr/bin/env python
# coding: utf-8

import os
import sys
import logging
import argparse
import collections

from wikiref.formats import DisambiguatedTripletReader

from wikiref.settings import CSV_TRIPLE_ARG_DELIMITER
from wikiref.settings import CSV_TERM_POS_DELIMITER
from wikiref.settings import CSV_TERM_NODE_DELIMITER
from wikiref.settings import CSV_NODE_NODE_DELIMITER
from wikiref.settings import CSV_NODE_SCORE_DELIMITER

from wikiref.merger import MergeIndex
from wikiref.merger import get_pattern


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ifile",    default=None,       type=str,
                        help="A path to the input csv file with the triples.")
    parser.add_argument("-o", "--odir",     default=None,       type=str,
                        help="Output directory with indexes.")
    parser.add_argument("-d", "--debug",    default=0,          type=int,
                        choices=(0, 1),     help="Dump debug information.")
    args = parser.parse_args()

    i_file = file(args.ifile, "rb") if args.ifile is not None else sys.stdin
    o_dir = args.odir

    reader = DisambiguatedTripletReader(i_file,
                                        CSV_TRIPLE_ARG_DELIMITER,
                                        CSV_TERM_POS_DELIMITER,
                                        CSV_TERM_NODE_DELIMITER,
                                        CSV_NODE_NODE_DELIMITER,
                                        CSV_NODE_SCORE_DELIMITER)

    lemma_dict = {}
    wnode_dict = {}
    wnode_stat = collections.Counter()
    triple_bins = dict()
    triple_index = MergeIndex(args.odir)

    for triple_id, (triple, triple_line) in enumerate(reader):

        # if triple_id != 2745743:
        #     continue

        if triple_id % 10000 == 0:
            logging.info("Processed %d triples." % triple_id)

        triple_pattern = get_pattern(triple)
        if triple_pattern is None:
            continue

        triplet_tuple = []
        for arg in triple.arguments:
            if arg is None:
                continue
            lemma, pos, nodes = arg
            if pos.startswith("NN"):
                triple_index.add_triple_line(triple_id, triple_line, triple_pattern)
                if lemma not in lemma_dict:
                    lemma_dict[lemma] = len(lemma_dict)
                wnode_stat[len(nodes)] += 1
                for node, weight in nodes:
                    if node not in wnode_dict:
                        wnode_dict[node] = len(wnode_dict)

                lemma_id = lemma_dict[lemma]
                nodes_id = [wnode_dict[n] for n,w in nodes]
                triplet_tuple.append((lemma_id, nodes_id))

        if len(triplet_tuple) == 0:
            continue

        if triple_pattern in triple_bins:
            triple_bins[triple_pattern].append((triple_id, triplet_tuple))
        else:
            triple_bins[triple_pattern] = [(triple_id, triplet_tuple)]

    triple_index.dump_cache()
    logging.info("Triple index is complete.")

    logging.info("Writing triple bins.")
    fl = sys.stdout
    for triple_bin_name, triple_tuples in triple_bins.iteritems():
        if len(triple_tuples) == 1:
            continue
        logging.info("Wring %s pattern: %d triples." % (triple_bin_name, len(triple_tuples)))
        fl.write("BIN\t%s\n" % triple_bin_name)
        for triple_id, triple_tuple in triple_tuples:
            fl.write(str(triple_id))
            for lemma_id, nodes_id in triple_tuple:
                fl.write("\t%d %s" % (lemma_id, ",".join([str(nid) for nid in nodes_id])))
            fl.write("\n")

    if args.debug == 1:
        logging.debug("Writing debug dump.")

        logging.debug("Writing lemmas ids.")
        with open(os.path.join(o_dir, "lemmas.txt"), "wb") as fl:
            for lemma, lemma_id in lemma_dict.iteritems():
                fl.write("%d\t%s\n" % (lemma_id, lemma))

        logging.debug("Writing nodes ids.")
        with open(os.path.join(o_dir, "nodes.txt"), "wb") as fl:
            for node, node_id in wnode_dict.iteritems():
                fl.write("%d\t%s\n" % (node_id, node))

        try:
            import numpy as np
        except ImportError:
            import numpypy as np

        logging.debug("Writing statistics.")
        with open(os.path.join(o_dir, "stat.txt"), "wb") as fl:
            for count_node, count_freq in wnode_stat.iteritems():
                fl.write("%d\t%d\n" % (count_node, count_freq))
            fl.write("median:   %d"   % np.median(wnode_stat.values()))
            fl.write("mean:     %.3f" % np.mean(wnode_stat.values()))
            fl.write("std:      %.3f" % np.std(wnode_stat.values()))


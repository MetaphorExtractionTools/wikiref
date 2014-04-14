#!/usr/bin/env python
# coding: utf-8

"""
Heuristical node overlap searcher.
"""

import os
import sys
import logging
import argparse

from wikiref.merger import find_overlaps


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--idir",     default=None,       type=str,
                        help="A path to the input csv file with the triples.")
    parser.add_argument("-d", "--debug",    default=0,          type=int,
                        choices=(0, 1),     help="Dump debug information.")
    args = parser.parse_args()

    if args.debug == 1:
        lemma_dict_fl = file(os.path.join(args.idir, "lemmas.txt"), "rb")
        wnode_dict_fl = file(os.path.join(args.idir, "nodes.txt"), "rb")
        lemma_id_pairs = [t.split("\t") for t in lemma_dict_fl.read().split("\n")]
        lemma_dict = {}
        for lemma_id, lemma in lemma_id_pairs[:(len(lemma_id_pairs) - 1)]:
            lemma_dict[int(lemma_id)] = lemma
        wnode_id_pairs = [t.split("\t") for t in wnode_dict_fl.read().split("\n")]
        wnode_dict = {}
        for wnode_id, wnode in wnode_id_pairs[:(len(wnode_id_pairs) - 1)]:
            wnode_dict[int(wnode_id)] = wnode
    else:
        wnode_dict = {}
        lemma_dict = {}

    triples = []
    bin_name = None

    processed = 0

    # Parsing input data in the following format:
    # BIN <bin_name>
    # <triple_id> <lemma_id> <node>,<node>[TAB]<lemma_id> <node>,<node>
    # <triple_id> <lemma_id> <node>,<node>[TAB]<lemma_id> <node>,<node>
    # BIN <bin_name>
    # ...
    # EOF

    for line in sys.stdin:
        line = line.rstrip()

        if line.startswith("BIN"):  # BIN start marker

            new_bin_name = line.split("\t")[1]  # bin name is in the second column

            # if len(triples) <= 32:
            if len(triples) > 1:

                logging.info("Processing %d triples. Bin: %s" % (len(triples), bin_name))

                found_overlaps = find_overlaps(triples)

                if len(found_overlaps) > 0:
                    logging.info("Found %d overlaps in %s." % (len(found_overlaps), bin_name))
                    try:
                        overlaps = [" ".join(map(str, overlap)) for overlap in found_overlaps]
                        sys.stdout.write("%s\t%s\n" % (bin_name, "\t".join(overlaps)))
                        processed += 1
                    except:
                        logging.error("Error occurred when writing overlaps of %s." % bin_name)

            triples = []
            bin_name = new_bin_name
            continue

        # Parse triple data line
        row = line.split("\t")
        triple_id = int(row[0])
        triplet = [triple_id, []]
        for i in xrange(1, len(row)):
            lemma_id_nodes_id = row[i].split(" ")
            try:
                if len(lemma_id_nodes_id) == 2 and len(lemma_id_nodes_id[1]) > 0:
                    lemma_id, nodes_id = lemma_id_nodes_id
                    nodes_id = tuple([int(nid) for nid in nodes_id.split(",")])
                elif len(lemma_id_nodes_id) == 1 or \
                     (len(lemma_id_nodes_id) == 2 and len(lemma_id_nodes_id[1]) == 0):
                    lemma_id = lemma_id_nodes_id[0]
                    nodes_id = tuple()
                else:
                    raise Exception("")
            except:
                logging.error("Parsing error. %r" % lemma_id_nodes_id)
                exit(0)

            lemma_id = int(lemma_id)
            triplet[1].append((lemma_id, nodes_id))

        triplet[1] = tuple(triplet[1])
        triples.append(triplet)




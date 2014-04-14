#!/usr/bin/env python
# coding: utf-8

import os
import sys
import leveldb
import logging
import argparse
import StringIO
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
    parser.add_argument("-i", "--ifile",        default=None,       type=str,
                        help="Stream of original triplestore file and generated triplestore.")
    parser.add_argument("-o", "--tmpdir",       default=None,       type=str,
                        help="Temporary directory needed to merge data.")
    parser.add_argument("-w", "--wordnet",      default=0,          type=int, choices=(0, 1),
                        help="Output wordnet nodes.")
    args = parser.parse_args()

    i_file = file(args.ifile, "rb") if args.ifile is not None else sys.stdin

    reader = DisambiguatedTripletReader(i_file,
                                        CSV_TRIPLE_ARG_DELIMITER,
                                        CSV_TERM_POS_DELIMITER,
                                        CSV_TERM_NODE_DELIMITER,
                                        CSV_NODE_NODE_DELIMITER,
                                        CSV_NODE_SCORE_DELIMITER)

    FINAL_DELIMITER = ", "
    FINAL_POS_DELIM = "-"

    def triple_to_kv(tr):
        tr_str = StringIO.StringIO()
        tr_str.write(tr.rel_type)
        for term_pos in tr.arguments:
            tr_str.write(FINAL_DELIMITER)
            if term_pos is None:
                tr_str.write("<NONE>")
            else:
                term, pos, nodes = term_pos
                if pos != "NN":
                    tr_str.write(term)
                    tr_str.write(FINAL_POS_DELIM)
                    tr_str.write(pos)
                else:
                    tr_str.write(term)

                    if args.wordnet == 1:
                        tr_str.write("(")
                        tr_str.write(str(nodes))
                        tr_str.write(")")

                    tr_str.write(FINAL_POS_DELIM)
                    tr_str.write(pos)

        for _ in xrange(len(tr.arguments), 5):
            tr_str.write(", <->")

        return tr_str.getvalue(), tr.frequency

    duplicate_resolver = collections.Counter()

    for tripleno, (triple, line) in enumerate(reader):


        key, val = triple_to_kv(triple)

        old_val = duplicate_resolver.get(key, -1)
        if val > old_val:
            duplicate_resolver[key] = val
            if old_val > 0:
                logging.info("%s: old frequency replaced %d -> %d " % (key, old_val, val))

        if tripleno % 10000 == 0:
            logging.info("Processed #%d triples." % tripleno)

    logging.info("There are %d triples in final triplestore." % len(duplicate_resolver))

    for triple, frequency in duplicate_resolver.most_common():
        sys.stdout.write("%s, %d\n" % (triple, frequency))
#!/usr/bin/env python
# coding: utf-8

import sys
import logging
import argparse

from wikiref.merger import MergeIndex
from wikiref.merger import merge_triples
from wikiref.formats import DisambiguatedTripletReader

from wikiref.settings import CSV_TRIPLE_ARG_DELIMITER
from wikiref.settings import CSV_TERM_POS_DELIMITER
from wikiref.settings import CSV_TERM_NODE_DELIMITER
from wikiref.settings import CSV_NODE_NODE_DELIMITER
from wikiref.settings import CSV_NODE_SCORE_DELIMITER



if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--idir",     default=None,       type=str,
                        help="A path to the input csv file with the triples.")
    parser.add_argument("-d", "--debug",    default=0,          type=int,
                        choices=(0, 1),     help="Dump debug information.")
    args = parser.parse_args()

    triple_index = MergeIndex(args.idir)

    reader = DisambiguatedTripletReader(None,
                                        CSV_TRIPLE_ARG_DELIMITER,
                                        CSV_TERM_POS_DELIMITER,
                                        CSV_TERM_NODE_DELIMITER,
                                        CSV_NODE_NODE_DELIMITER,
                                        CSV_NODE_SCORE_DELIMITER)

    ofile = sys.stdout

    for lineno, line in enumerate(sys.stdin):
        line = line.rstrip("\n")
        row = line.split("\t")
        bin_name = row[0]
        overlaps = row[1:]
        try:

            bin_triples = triple_index.get_bin(bin_name)

        except KeyError:
            logging.error("Pattern not found #%d." % lineno)
            continue
        for overlap in overlaps:
            overlap = overlap.split()
            if len(overlap) < 2:
                continue

            try:
                new_triple = merge_triples(overlap, bin_triples, reader.map_csv_line)
                if new_triple is None:
                    continue
            except KeyError:
                continue

            tr = new_triple


            ofile.write(tr.rel_type)
            for term_pos in tr.arguments:
                ofile.write(CSV_TRIPLE_ARG_DELIMITER)
                if term_pos is None:
                    ofile.write("<NONE>")
                else:
                    term, pos, nodes = term_pos
                    if pos != "NN":
                        ofile.write(term)
                        ofile.write(CSV_TERM_POS_DELIMITER)
                        ofile.write(pos)
                    else:
                        lemmas = term.split("&&")

                        ofile.write(term)

                        ofile.write(CSV_TERM_POS_DELIMITER)
                        ofile.write(pos)
                        ofile.write(CSV_TERM_NODE_DELIMITER)
                        ofile.write(CSV_NODE_NODE_DELIMITER.join([CSV_NODE_SCORE_DELIMITER.join((n, "%.8f" % s)) for n,s in nodes]))

            ofile.write(CSV_TRIPLE_ARG_DELIMITER)
            ofile.write(str(tr.frequency))

            ofile.write("\n")
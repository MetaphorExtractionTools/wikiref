#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import os
import sys
import logging
import argparse


from wikiref.yago import YagoTypes
from wikiref.yago import YagoTaxonomy
from wikiref.yago import YagoClassDict
from wikiref.yago import YagoClassSearch

from wikiref.formats import TripleStoreReader
from wikiref.disambig import MinClassDisambigSolver

from wikiref.settings import CSV_TRIPLE_ARG_DELIMITER
from wikiref.settings import CSV_TERM_POS_DELIMITER
from wikiref.settings import CSV_TERM_NODE_DELIMITER
from wikiref.settings import CSV_NODE_NODE_DELIMITER
from wikiref.settings import CSV_NODE_SCORE_DELIMITER

from wikiref.settings import INDEX_YAGO_TYPES_DIRNAME
from wikiref.settings import INDEX_YAGO_TAXONOMY_DIRNAME
from wikiref.settings import INDEX_YAGO_CLASS_DICT_DIRNAME
from wikiref.settings import INDEX_YAGO_CLASS_SEARCH_DIRNAME


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--index",    default="index",    type=str,
                        help="A path to the database directory which will be created.")
    parser.add_argument("-i", "--ifile",    default=None,       type=str,
                        help="A path to the input csv file with the triples.")
    parser.add_argument("-o", "--ofile",    default=None,       type=str,
                        help="A path to the result file.")
    parser.add_argument("-n", "--names",    default=None,       type=str,
                        help="A path to the names set file.")
    parser.add_argument("-n", "--lang",    default=None,       type=str,
                        help="Input language.")
    parser.add_argument("-l", "--delim",    default=245,        type=int,
                        help="Triple store CSV delimiter.")
    parser.add_argument("-t", "--test",    default=0,           type=int, choices=(0, 1),
                        help="Run tests.")


    args = parser.parse_args()

    ifile = file(args.ifile, "rb") if args.ifile is not None else sys.stdin
    ofile = file(args.ofile, "wb") if args.ofile is not None else sys.stdout
    if args.names is not None:
        names_set = set(open(args.names, "rb").read().split("\n"))
    else:
        names_set = set()

    index_dir = args.index

    logging.basicConfig(level=logging.INFO)
    logging.info("Index directory: %s" % index_dir)
    logging.info("Input triples file: %r" % ifile)
    logging.info("Output file: %r" % ofile)

    yago_class_dict = YagoClassDict(os.path.join(index_dir, INDEX_YAGO_CLASS_DICT_DIRNAME))
    logging.info("Yago Class Dict: %r" % yago_class_dict)

    yago_class_search = YagoClassSearch(os.path.join(index_dir, INDEX_YAGO_CLASS_SEARCH_DIRNAME))
    logging.info("Yago Class Search: %r" % yago_class_search)

    yago_taxonomy = YagoTaxonomy(os.path.join(index_dir, INDEX_YAGO_TAXONOMY_DIRNAME))
    logging.info("Yago Taxonomy: %r" % yago_taxonomy)

    yago_types = YagoTypes(os.path.join(index_dir, INDEX_YAGO_TYPES_DIRNAME))
    logging.info("Yago Types: %r" % yago_types)

    solver = MinClassDisambigSolver(yago_class_dict,
                                    yago_class_search,
                                    yago_taxonomy,
                                    yago_types,
                                    names_set)

    delimiter = "," if args.delim is None else chr(args.delim)

    reader = TripleStoreReader(ifile, csv_triple_arg_delimiter=delimiter)

    def has_letter(lemma):
        for ch in lemma:
            if ch in string.letters:
                return True
        return False

    def dismabiguate_eng(lemmas):
        long_lemma = " ".join(lemmas)
        nodes_set = yago_class_dict[long_lemma]

        if nodes_set is not None and nodes_set.instance_count() == 0 and nodes_set.size() > 0:
            nodes = nodes_set.nodes
            score = 1.0 / len(nodes)
            logging.info(nodes)
            return [(node, score) for node in nodes]

        elif nodes_set is not None and nodes_set.instance_count() > 0:
            nodes = solver.disambiguate(lemmas, return_size=-1, depth=2, debug=True, try_lca=False)
            return nodes

        nodes_set = yago_class_dict[lemmas[-1]]
        if nodes_set is not None and nodes_set.instance_count() == 0 and nodes_set.size() > 0:
            nodes = nodes_set.nodes
            score = 1.0 / len(nodes)
            return [(node, score) for node in nodes]

        nodes = solver.disambiguate(lemmas, return_size=-1, depth=2, debug=True, try_lca=False)
        if len(nodes) == 0:
            nodes = solver.disambiguate(lemmas, return_size=-1, depth=2, debug=True, try_lca=True)
        return nodes


    def load_cache():
        cache_fl = open("/Volumes/1TB/wikiref_result/cache.txt", "rb")
        cache = {}
        for line in cache_fl:
            row = line.rstrip("\n").split("\t")
            lemma = row[1]
            nodes = [n.split(" ") for n in row[2].split(";") if len(n)]
            if len(nodes) == 0:
                continue
            nodes = [(n, float(s)) for n,s in nodes]
            if lemma not in cache:
                cache[lemma] = nodes
        return cache

    cache = load_cache()
    logging.info("Loaded %d entries from cache." % len(cache))

    for tr_no, tr in enumerate(reader):

        if tr_no % 10000 == 0:
            logging.info("Processed %d triples." % tr_no)

        ofile.write(tr.rel_type)
        error_occured = False
        for term_pos in tr.arguments:
            ofile.write(CSV_TRIPLE_ARG_DELIMITER)
            if term_pos is None:
                ofile.write("<NONE>")
            else:
                term, pos = term_pos
                if pos != "NN":
                    ofile.write(term)
                    ofile.write(CSV_TERM_POS_DELIMITER)
                    ofile.write(pos)
                else:
                    lemmas = sorted(term.split("&&"))
                    lemmas = [lemma for lemma in lemmas if has_letter(lemma)]
                    lemmas = [l.replace("_", " ").replace("-", " ") for l in lemmas]

                    lemma_key = "&".join(lemmas)

                    if len(lemmas) > 1 and args.test == 1:
                        sys.stderr.write("Lemmas: %s\n" % ", ".join(lemmas))

                        nodes = cache.get(lemma_key)
                        if nodes is None:
                            if len(lemmas) > 1:
                                logging.info("Not found %r" % lemma_key)
                            nodes = solver.disambiguate(lemmas, return_size=-1, depth=2, debug=True, try_lca=False)

                        if len(nodes) == 0:
                            nodes = solver.disambiguate(lemmas, return_size=-1, depth=2, debug=True, try_lca=True)

                        sys.stderr.write("FINAL_RESULT: %s" % " ".join(lemmas))
                        sys.stderr.write(" => ")
                        sys.stderr.write("[%s]" % ", ".join([n for n, w in nodes]))
                        sys.stderr.write("\n\n\n\n\n\n")
                    else:

                        nodes = cache.get(lemma_key)

                        if nodes is None:
                            if len(lemmas) > 1:
                                logging.info("Not found %r" % lemma_key)
                            nodes = solver.disambiguate(lemmas, return_size=-1, depth=2, debug=False, try_lca=False)
                        if nodes is None or len(nodes) == 0:
                            nodes = solver.disambiguate(lemmas, return_size=-1, depth=2, debug=False, try_lca=True)

                    ofile.write(term)

                    ofile.write(CSV_TERM_POS_DELIMITER)
                    ofile.write(pos)
                    ofile.write(CSV_TERM_NODE_DELIMITER)
                    ofile.write(CSV_NODE_NODE_DELIMITER.join([CSV_NODE_SCORE_DELIMITER.join((n, "%.8f" % s))
                                                              for n, s in nodes]))
        if not error_occured:

            ofile.write(CSV_TRIPLE_ARG_DELIMITER)
            ofile.write(str(tr.frequency))

            ofile.write("\n")
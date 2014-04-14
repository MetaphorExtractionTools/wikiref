#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

"""
This scripts creates inverted index which maps yago labels to yago classes or instances.
For usage examples, please see examples/creadte_indexes.sh.
"""

import gc
import os
import sys
import leveldb
import logging
import fileinput
import argparse

from wikiref.util import extract_label
from wikiref.util import flush_dict_to_ldb

from wikiref.settings import LDB_ARRAY_DELIM
from wikiref.settings import INDEX_YAGO_TSV_DELIM
from wikiref.settings import INDEX_YAGO_CLASS_DICT_DIRNAME


logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", default=None, type=str, help="List of input files, delimited by colons.")
parser.add_argument("-o", "--odir", default=None, type=str, help="List of input files, delimited by colons.")
parser.add_argument("-r", "--rels", default="<isPreferredMeaningOf> <redirectedFrom>", type=str,
                    help="List of relations to index separated by spaces.")
parser.add_argument("-l", "--lang", default="eng", type=str, help="List of languages to to index.")
args = parser.parse_args()

if args.input is None:
    i_file = sys.stdin
else:
    i_file = fileinput.input(args.input.split(":"))

logging.info("Input: %r" % args.input)
logging.info("Output: %r" % args.odir)


CUR_SIZE = 0
MAX_SIZE = 100000 * 128
LDB = leveldb.LevelDB(os.path.join(args.odir, INDEX_YAGO_CLASS_DICT_DIRNAME))

index_cache = dict()
allowed_rels = frozenset(args.rels.split(" "))
allowed_langs = frozenset(args.lang.split(":"))

logging.info("Allowed relations: %r" % allowed_rels)
logging.info("Allowed languages: %r" % allowed_langs)


for line in i_file:

    row = line.split(INDEX_YAGO_TSV_DELIM)
    rel = row[2]

    if rel not in allowed_rels:
        continue

    node = row[1]
    label_lang = row[3]

    try:
        label, lang = extract_label(label_lang)
    except ValueError:
        logging.error("Unable to extract label from '%r'." % label_lang)
        continue

    if label is None or lang not in allowed_langs:
        continue

    label = label.lower()

    if label in index_cache:
        index_cache[label].append(node)
    else:
        index_cache[label] = [node]
    CUR_SIZE += 1

    if CUR_SIZE > MAX_SIZE:
        flush_dict_to_ldb(LDB, index_cache)
        index_cache = dict()
        CUR_SIZE = 0
        gc.collect()


flush_dict_to_ldb(LDB, index_cache)
i_file.close()
logging.info("[DONE]")
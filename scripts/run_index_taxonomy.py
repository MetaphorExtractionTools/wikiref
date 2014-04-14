#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

"""
This scripts creates inverted index which maps from label words into yago classes or instances.
For usage examples, please see examples/creadte_indexes.sh.
"""

import os
import sys
import leveldb
import logging
import fileinput

from wikiref.util import flush_dict_to_ldb

from wikiref.settings import LDB_ARRAY_DELIM
from wikiref.settings import INDEX_TAXONOMY_REL
from wikiref.settings import INDEX_YAGO_TSV_DELIM
from wikiref.settings import INDEX_YAGO_TAXONOMY_DIRNAME


logging.basicConfig(level=logging.INFO)

try:
    _, yago_taxonomy_file, output_dir = sys.argv
except Exception:
    logging.error("usage: %s <yago_taxonomy_file> <output_dir>" % __file__)
    exit(1)


CUR_SIZE = 0
MAX_SIZE = 100000 * 128
LDB = leveldb.LevelDB(os.path.join(output_dir, INDEX_YAGO_TAXONOMY_DIRNAME))


input_fl = fileinput.input((
    yago_taxonomy_file,
))

index_cache = dict()


for line in input_fl:

    row = line.split(INDEX_YAGO_TSV_DELIM)
    rel = row[2]

    if rel != INDEX_TAXONOMY_REL:
        continue


    child_class = row[1]
    parent_class = row[3]

    if len(child_class) == 0 or len(parent_class) == 0:
        continue

    if child_class in index_cache:
        index_cache[child_class].add(parent_class)
    else:
        index_cache[child_class] = {parent_class}
    CUR_SIZE += 1

    if CUR_SIZE > MAX_SIZE:
        flush_dict_to_ldb(LDB, index_cache)
        index_cache = dict()
        CUR_SIZE = 0


flush_dict_to_ldb(LDB, index_cache)


input_fl.close()
logging.info("[DONE]")
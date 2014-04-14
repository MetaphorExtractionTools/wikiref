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
from wikiref.settings import INDEX_TYPE_REL
from wikiref.settings import INDEX_YAGO_TSV_DELIM
from wikiref.settings import INDEX_YAGO_TYPES_DIRNAME


logging.basicConfig(level=logging.INFO)

try:
    _, yago_types_file, output_dir = sys.argv
except Exception:
    logging.error("usage: %s <yago_types_file> <output_dir>" % __file__)
    exit(1)


CUR_SIZE = 0
MAX_SIZE = 100000 * 128
LDB = leveldb.LevelDB(os.path.join(output_dir, INDEX_YAGO_TYPES_DIRNAME))

input_fl = fileinput.input((
    yago_types_file,
))

index_cache = dict()


for line in input_fl:

    row = line.split(INDEX_YAGO_TSV_DELIM)
    rel = row[2]

    if rel != INDEX_TYPE_REL:
        continue


    instance = row[1]
    instance_class = row[3]

    if len(instance) == 0 or len(instance_class) == 0:
        continue

    if instance in index_cache:
        index_cache[instance].add(instance_class)
    else:
        index_cache[instance] = {instance_class}
    CUR_SIZE += 1

    if CUR_SIZE > MAX_SIZE:
        flush_dict_to_ldb(LDB, index_cache)
        index_cache = dict()
        CUR_SIZE = 0


flush_dict_to_ldb(LDB, index_cache)


input_fl.close()
logging.info("[DONE]")
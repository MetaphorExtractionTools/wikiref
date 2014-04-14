# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import re
import leveldb
import logging

from wikiref.settings import LDB_ARRAY_DELIM

from nltk.tokenize.punkt import PunktWordTokenizer

RE_WORDSPLIT = re.compile("\W", re.UNICODE)
LABEL_LANG_RE = re.compile("\"(.+)\"@(.+)")
TOKENIZER = PunktWordTokenizer()


def extract_parts(label_str):
    label_str = label_str.decode("utf-8").lower()
    parts = TOKENIZER.tokenize(label_str)
    return [p.encode("utf-8") for p in parts if len(p)]


def extract_label(label_str):
    matches = LABEL_LANG_RE.findall(label_str)
    if len(matches) != 1:
        raise ValueError("Wrong label format '%r'." % label_str)
    matches = matches[0]
    if len(matches) == 2:
        return matches[0], matches[1]
    else:
        raise ValueError("Wrong label format '%r'." % label_str)


def flush_dict_to_ldb(ldb, cache, ignore_kv_duplicates=False):
    """
    Adds dict: key->[values] into LevelDb.
    """
    batch = leveldb.WriteBatch()
    for key, new_values in cache.iteritems():
        try:
            values = set(ldb.Get(key).split(LDB_ARRAY_DELIM))
            values.update(new_values)
        except KeyError:
            values = set(new_values)
        values = sorted(values)
        if ignore_kv_duplicates:
            batch.Put(key, LDB_ARRAY_DELIM.join(filter(lambda val: val != key, values)))
        else:
            batch.Put(key, LDB_ARRAY_DELIM.join(values))
    ldb.Write(batch)
    logging.info("Flushed %d items." % len(cache))

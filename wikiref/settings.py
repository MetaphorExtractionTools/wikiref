# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

#CSV_TRIPLE_ARG_DELIMITER  = ", "
#CSV_TERM_POS_DELIMITER    = "~"
#CSV_TERM_NODE_DELIMITER   = "="
#CSV_NODE_NODE_DELIMITER   = "; "
#CSV_NODE_SCORE_DELIMITER  = "/"

CSV_TRIPLE_ARG_DELIMITER  = chr(255)
CSV_TERM_POS_DELIMITER    = chr(254)
CSV_TERM_NODE_DELIMITER   = chr(253)
CSV_NODE_NODE_DELIMITER   = chr(252)
CSV_NODE_SCORE_DELIMITER  = chr(251)

LDB_ARRAY_DELIM           = chr(244)

INDEX_YAGO_TSV_DELIM            = "\t"
INDEX_YAGO_CLASS_DICT_DIRNAME   = "yago_class_dict.ldb"
INDEX_YAGO_CLASS_SEARCH_DIRNAME = "yago_class_search.ldb"
INDEX_YAGO_TAXONOMY_DIRNAME     = "yago_taxonomy.ldb"
INDEX_YAGO_TYPES_DIRNAME        = "yago_types.ldb"

INDEX_TAXONOMY_REL              = "rdfs:subClassOf"
INDEX_CLASS_REL                 = "rdfs:label"
INDEX_TYPE_REL                  = "rdf:type"


MERGING_INDEX_TRIPLE_ID_DELIMITER   = chr(243)
MERGING_INDEX_TRIPLE_LINE_DELIMITER = chr(242)

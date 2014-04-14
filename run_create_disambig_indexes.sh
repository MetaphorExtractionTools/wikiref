#!/usr/bin/env bash

source env.sh

pypy scripts/run_index_class_dict.py                                            \
    --input $DATADIR/yagoLabels.tsv:$DATADIR/yagoLabels.experimental.csv        \
    --odir $INDEXDIR                                                            \
    --rels "<isPreferredMeaningOf> <redirectedFrom>"                            \
    --lang "eng"

pypy scripts/run_index_class_search.py                                            \
    --input $DATADIR/yagoLabels.tsv:$DATADIR/yagoLabels.experimental.csv        \
    --odir $INDEXDIR                                                            \
    --rels "<isPreferredMeaningOf> <redirectedFrom>"             \
    --lang "eng"

pypy scripts/run_index_taxonomy.py  \
    $DATADIR/yagoSimpleTaxonomy.tsv \
    $INDEXDIR

pypy scripts/run_index_types.py  \
    $DATADIR/yagoSimpleTypes.tsv \
    $INDEXDIR
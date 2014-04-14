#!/usr/bin/env bash

source env.sh

pypy scripts/run_disambiguate_nouns.py      \
    --index $INDEXDIR                 \
    --names $DATADIR/names_$1.txt     \
    --delim 245 \
    < /dev/stdin
    > /dev/stdout
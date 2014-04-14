#!/usr/bin/env bash

# Load envieronment variables.
source env.sh

pypy scripts/run_find_overlaps.py \
    --idir $TEMPDIR/merging \
    --debug 1 \
    < /dev/stdin
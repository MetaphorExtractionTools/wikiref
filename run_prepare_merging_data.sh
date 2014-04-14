#!/usr/bin/env bash

# Load envieronment variables.
source env.sh

python scripts/run_prepare_merging_data.py \
    --odir $TEMPDIR/merging \
    --debug 1 \
    < /dev/stdin
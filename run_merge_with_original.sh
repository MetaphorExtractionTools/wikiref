#!/usr/bin/env bash

source env.sh

pypy scripts/run_merge_with_original.py     \
    --ifile     /dev/stdin                  \
    --tmpdir    $TEMPDIR/final_merge_tmp    \
    > /dev/stdout
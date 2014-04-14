#!/usr/bin/env bash

# Load envieronment variables.
source env.sh

# Step 1. Create disambiguaion indexes for Yago data.
./run_create_disambig_indexes.sh

# Step 2. Complete disambiguation for nouns.
bzcat $INPUT_TRIPLESTORE \
| pypy scripts/fix_delimiters.py 245 \
| ./run_disambiguate_nouns.sh en     \
| bzip2 -9 > $TEMPDIR/triplestore.disambiguated.txt.bz2

# Step 3. Prepare disambiguated data for merging.
bzcat < $TEMPDIR/triplestore.disambiguated.txt.bz2 \
| ./run_prepare_merging_data.sh                    \
| bzip2 -9 > $TEMPDIR/merging/triples.txt.bz2

# Step 4. Find all everlaps.
bzcat < $TEMPDIR/merging/triples.txt.bz2 \
| ./run_find_overlaps.sh                 \
| bzip2 -9 > $TEMPDIR/merging/overlaps.txt.bz2

# Step 5. Merge overlaping triples and compute overlap frequencies.
bzcat < $TEMPDIR/merging/overlaps.txt.bz2 \
| ./run_merge_overlaps.sh                 \
| pbzip2 -9 > $TEMPDIR/merging/new_triples.txt.bz2

# Step 6. Merge original triple store with new triples
bzcat $TEMPDIR/triplestore.disambiguated.txt.bz2 \
$TEMPDIR/merging/new_triples.txt.bz2             \
| ./run_merge_with_original.sh                   \
| pbzip2 -9 > $TEMPDIR/final_output.csv.bz2


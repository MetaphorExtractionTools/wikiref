#!/usr/bin/env bash

TEMPDIR=~/wikiref_temp
DATADIR=~/wikiref_data
INDEXDIR=$TEMPDIR/index

INPUT_TRIPLESTORE=$DATADIR/new_triples.txt.bz2

WIKIREF=$PWD
HUGIN=~/code/isi/hugin
SEAR=~/code/isi/sear
METAPHOR=~/code/isi/metaphor

export PYTHONPATH=$HUGIN:$SEAR:$METAPHOR:$WIKIREF:PYTHONPATH

#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# CORENLP
URL="http://nlp.stanford.edu/software/stanford-corenlp-full-2017-06-09.zip"
LOC_DIR="$DIR/stanford-corenlp-full-2017-06-09"
if [[ ! -d "$LOC_DIR" ]]; then
    mkdir -p "$LOC_DIR"
    wget $URL -O ${LOC_DIR}.zip
    unzip ${LOC_DIR}.zip -d $DIR
fi

LIBS="$DIR/libs"
[ -d $LIBS ] || mkdir -p $LIBS

# ARGS4J
URL="http://central.maven.org/maven2/args4j/args4j/2.33/args4j-2.33.jar"
LOC_FILE="$LIBS/args4j-2.33.jar"
if [[ ! -f $LOC_FILE ]]; then
    wget $URL -O $LOC_FILE
fi

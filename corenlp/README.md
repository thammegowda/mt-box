# CoreNLP Annotator

The `corenlp.scala` is an annotator based on Stanford CoreNLP.
It has three objectives:
1. Fast - No network IO as in python APIs. Meant to annotate large english corpus quickly.
2. Unix pipe friendly - just cat the file and pipe it to this. then take it out from STDOUT, awk to take the column you need. Or use -in and -out file paths.
3. Flexible - its a script, edit the script when you need - no need to compile whole project as in Java


## Setup 

`bash setup.sh` to download the necessary libs.

## Example

$ head myfile.txt  | ./corenlp.scala

## Usage 

```
$ ./corenlp.scala -h
Usage::
 -delim VAL  : Delimiter. Default is \t (default: 	)
 -h (--help) : Show this help message (default: true)
 -in VAL     : Input file. Default=STDIN
 -out VAL    : Output file. Default=STDOUT
 -threads N  : Number of Threads to use. (default=N-1)
``` 


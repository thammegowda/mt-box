#!/bin/sh
# Initial Author = Thamme Gowda tg@isi.edu
# Created Date = Oct 26, 2017
# Purpose =
# CoreNLP annotator for english text with following features:
#    1. fast for annotating large corpus -- no network io like in python APIs
#    2. easy to glue with bash pipes -- maps text from STDIN to STDOUT by default
#    3. Easy to tweak -- edit the scala script below, this is just a beginning
#
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLASSPATH="$DIR/libs/*:$DIR/stanford-corenlp-full-2017-06-09/*"
SCALA_HOME="/Users/tg/bin/scala-2.12.4"
exec $SCALA_HOME/bin/scala -classpath ".:$CLASSPATH" -savecompiled "$0" "$@"
!#

import java.io.{File, PrintWriter}

import edu.stanford.nlp.pipeline._
import edu.stanford.nlp.ling.{CoreAnnotations, CoreLabel}
import edu.stanford.nlp.util.{CoreMap, PropertiesUtils}
import org.kohsuke.args4j._

import collection.JavaConverters._
import scala.io.Source
import scala.collection._


/**
  * All CLI args go here
  */
object CliArgs {

  @Option(name = "-h", aliases = Array("--help"), help=true, usage = "Show this help message")
  var help:Boolean = _

  @Option(name = "-in", required = false, usage = "Input file. Default=STDIN")
  var input: String = _

  @Option(name = "-out", required = false, usage = "Output file. Default=STDOUT")
  var output: String = _

  @Option(name = "-delim", required = false, usage = "Delimiter. Default is \\t")
  var delim = "\t"

  def parseArgs(args:Array[String]): Unit ={
    val parser = new CmdLineParser(this)
    try {
      parser.parseArgument(args.toSeq.asJavaCollection)
      if (CliArgs.help) {
        println("Usage::")
        parser.printUsage(System.out)
        System.exit(0)
      }
    } catch {
      case e: CmdLineException =>
        print(s"Error:${e.getMessage}\n Usage:\n")
        parser.printUsage(System.out)
        System.exit(1)
    }
  }
}
CliArgs.parseArgs(args)

/**
  * Record class for organizing records
  * @param text input text
  * @param words seq of words
  * @param lemmas seq of lemma words
  * @param posTags seq of POS tags
  */
case class Record(text:String, words:mutable.Seq[String],
                  lemmas: mutable.Seq[String], posTags: mutable.Seq[String]) {

  def format(): String = {
    text.replace(CliArgs.delim, " ") + CliArgs.delim +
      words.mkString(" ") + CliArgs.delim +
      lemmas.mkString(" ") + CliArgs.delim +
      posTags.mkString(" ")
  }
}

// creates a StanfordCoreNLP object, with POS tagging, lemmatization, NER, parsing, and coreference resolution
val props = PropertiesUtils.asProperties(
  "annotators", "tokenize,ssplit,pos,lemma",
  "ssplit.isOneSentence", "true",
  "parse.model", "edu/stanford/nlp/models/srparser/englishSR.ser.gz",
  "tokenize.language", "en")

val corenlp = new StanfordCoreNLP(props)

/**
  * Annotates text
  * @param text text to be annotated
  * @return a Record object
  */
def annotate(text:String): Record = {
  val doc = new Annotation(text)
  corenlp.annotate(doc)
  var words = new mutable.ArrayBuffer[String]()
  var posTags = new mutable.ArrayBuffer[String]
  var lemmas = new mutable.ArrayBuffer[String]

  val sentences = doc.get(classOf[CoreAnnotations.SentencesAnnotation]).asScala

  for (sentence: CoreMap <- sentences) {
    val tokens = sentence.get(classOf[CoreAnnotations.TokensAnnotation]).asScala
    for (token: CoreLabel <- tokens) {
      val word = token.get(classOf[CoreAnnotations.TextAnnotation])
      val pos = token.get(classOf[CoreAnnotations.PartOfSpeechAnnotation])
      val lemma = token.get(classOf[CoreAnnotations.LemmaAnnotation])
      words += word
      posTags += pos
      lemmas += lemma
    }
  }
  Record(text, words, lemmas, posTags)
}

//  Up stream to read input
val input = if (CliArgs.input != null) Source.fromFile(CliArgs.input) else Source.stdin
// Down Stream to consume output
var output = if (CliArgs.output != null)
            new PrintWriter(new File(CliArgs.output))
            else new PrintWriter(System.out)
try {
  for (line <- input.getLines()) {
    output.write(annotate(line).format())
    output.write("\n")
  }
} finally {
  output.flush()
  if (CliArgs.output != null) {
    output.close()
  }
}

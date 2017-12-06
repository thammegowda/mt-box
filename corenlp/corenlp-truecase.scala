#!/bin/sh
# Initial Author = Thamme Gowda tg@isi.edu
# Created Date = Dec 6, 2017
# Purpose =
# CoreNLP Sentence Splitter
#
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CLASSPATH="$DIR/libs/*:$DIR/stanford-corenlp-full-2017-06-09/*"
which scala > /dev/null; [[ $? -eq 0 ]] || echo 'scala not found. Download and add it to PATH. See https://www.scala-lang.org/download/'
exec scala -classpath ".:$CLASSPATH" -savecompiled "$0" "$@"
!#

import java.io.{File, PrintWriter}

import org.kohsuke.args4j._

import collection.JavaConverters._
import scala.io.Source
import edu.stanford.nlp.pipeline._
import edu.stanford.nlp.ling.CoreAnnotations
import edu.stanford.nlp.util.{CoreMap, PropertiesUtils}


/**
  * CLI args Parser
  */
object CliArgs {

  @Option(name = "-h", aliases = Array("--help"), help=true, usage = "Show this help message")
  var help:Boolean = _

  @Option(name = "-in", usage = "Input file. Default=STDIN")
  var input: String = _

  @Option(name = "-out", usage = "Output file. Default=STDOUT")
  var output: String = _



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

//  Up stream to read input
val input = if (CliArgs.input != null) Source.fromFile(CliArgs.input) else Source.stdin
// Down Stream to consume output
var output = if (CliArgs.output != null) new PrintWriter(new File(CliArgs.output)) else new PrintWriter(System.out)
val props = PropertiesUtils.asProperties(
  "annotators", "tokenize,ssplit,truecase",
  "ssplit.isOneSentence", "true")

val corenlp = new StanfordCoreNLP(props)

for (line <- input.getLines()) {
  if (!line.trim.isEmpty) {
    val doc = new Annotation(line)
    corenlp.annotate(doc)
    val sentences = doc.get(classOf[CoreAnnotations.SentencesAnnotation]).asScala
    for (sent: CoreMap <- sentences) {
      val toks = sent.get(classOf[CoreAnnotations.TokensAnnotation])
      val res = toks.asScala.map(t => t.get(classOf[CoreAnnotations.TrueCaseTextAnnotation]))
      output.println(res.mkString(" "))
    }
    //output.println() // empty line between records
  }
}

output.flush()
if (CliArgs.output != null) {
  output.close()
}
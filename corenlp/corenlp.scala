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
CLASSPATH=`echo $DIR/libs/* $DIR/stanford-corenlp-full-*/* |tr ' ' ':'`
export PATH="${PATH}:`echo $DIR/scala-*/bin`"
which scala > /dev/null; [[ $? -eq 0 ]] || echo 'scala not found. Download and add it to PATH. See https://www.scala-lang.org/download/'
exec scala -classpath ".:$CLASSPATH" -savecompiled "$0" "$@"
!#

import java.io.{File, PrintWriter}
import java.util.concurrent.{ArrayBlockingQueue, PriorityBlockingQueue, ThreadPoolExecutor, TimeUnit}

import edu.stanford.nlp.pipeline._
import edu.stanford.nlp.ling.{CoreAnnotations, CoreLabel}
import edu.stanford.nlp.util.{CoreMap, PropertiesUtils}
import org.kohsuke.args4j._

import collection.JavaConverters._
import scala.io.Source
import scala.collection._

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

  @Option(name = "-delim", usage = "Delimiter. Default is \\t")
  var delim = "\t"

  @Option(name = "-threads", usage = "Number of Threads to use")
  var nThreads:Int = Math.max(2, Runtime.getRuntime.availableProcessors() - 1)

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
case class Record(seq:Long, text:String, words:mutable.Seq[String],
                  lemmas: mutable.Seq[String], posTags: mutable.Seq[String]) extends Comparable[Record]{

  def format(): String = Array(
    s"$seq",
    text.replace(CliArgs.delim, " "),
    words.mkString(" "),
    lemmas.mkString(" "),
    posTags.mkString(" ")).mkString(CliArgs.delim)

  override def compareTo(o: Record): Int = java.lang.Long.compare(this.seq, o.seq)
}

// creates a StanfordCoreNLP object, with POS tagging, lemmatization
val props = PropertiesUtils.asProperties(
  "annotators", "tokenize,ssplit,pos,lemma",
  "ssplit.isOneSentence", "true",
  "parse.model", "edu/stanford/nlp/models/srparser/englishSR.ser.gz",
  "tokenize.language", "en")

val corenlp = new StanfordCoreNLP(props)

//val pQueue = collection.mutable.PriorityQueue[Record]()(Ordering.by(orderBy)).reverse
// NOTE: Scala PQueue is not thread safe, so using java PQueue
val pQueue = new PriorityBlockingQueue[Record]()

/**
  * Annotates text
  * @param text text to be annotated
  * @return a Record object
  */
def annotate(seq:Long, text:String): Record = {
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
  Record(seq, text, words, lemmas, posTags)
}

val EMPTY = mutable.Seq[String]()
val sleepTime = 25 //milli seconds

class AnnTask(seq:Long, text:String) extends Runnable {
  override def run(): Unit = {
    try pQueue.add(annotate(seq, text))
    catch {
      case _: Exception => pQueue.add(Record(seq, text, EMPTY, EMPTY, EMPTY))
    }
  }
}

// Thread pool
private val pool = new ThreadPoolExecutor(CliArgs.nThreads, CliArgs.nThreads, 1, TimeUnit.MINUTES,
                        new ArrayBlockingQueue[Runnable](CliArgs.nThreads * 4))

//  Up stream to read input
val input = if (CliArgs.input != null) Source.fromFile(CliArgs.input) else Source.stdin
// Down Stream to consume output
var output = if (CliArgs.output != null) new PrintWriter(new File(CliArgs.output)) else new PrintWriter(System.out)

@volatile var readerSeq:Long = 1
@volatile var writerSeq = readerSeq
@volatile var readerDone = false


val writer = new Thread {
  override def run(): Unit = {
    while (!(readerSeq == writerSeq && readerDone)) {
      // when to pack-up the loop
      //wait until the correct sequence shows up in the top of heap
      while (pQueue.isEmpty || pQueue.peek().seq != writerSeq) {
        Thread.sleep(sleepTime)
      }
      // When correct item is ready
      if (!pQueue.isEmpty) {
        if (pQueue.peek().seq == writerSeq) {
          val rec = pQueue.poll()
          output.write(rec.format())
          output.write("\n")
          writerSeq += 1
        }
      }
    }
  }
}

val reader = new Thread {
  override def run(): Unit = {
    for (line <- input.getLines()) {
      if (pool.getQueue.size() >= 2 * CliArgs.nThreads){
        Thread.sleep(sleepTime)
      }
      pool.execute(new AnnTask(readerSeq, line))
      readerSeq += 1
    }
    readerDone = true // end of reading
  }
}

reader.start()
writer.start()

reader.join()
writer.join()
pool.shutdown()

output.flush()
if (CliArgs.output != null) {
  output.close()
}

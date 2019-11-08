#!/bin/bash

FILE=$1
PASS=$2
TMP_FILE=/tmp/out

check_result_file() {
  RESULT_FILE=$1
  HINT=${2:""}
  if [ ! -f "$RESULT_FILE" ]; then
    echo "Nothing found (with no/default password)"
    return
  fi

  SIZE=`stat -c %s "$RESULT_FILE"`

  if [ ! "`file $RESULT_FILE`" = "$RESULT_FILE: data" ] && [ $SIZE -ge 1 ]; then
    echo "Found something!!!"
    echo "Result size: $SIZE (type: '`file $RESULT_FILE`')"
    echo "<hr>"
    head -n 71 $RESULT_FILE
    echo "<hr>"
  elif [ ! $SIZE -ge 1 ]; then
    echo "Nothing found/no result with that password"
  elif [ "`file $RESULT_FILE`" = "$RESULT_FILE: data" ] && [ $SIZE -ge 1 ]; then
    echo "Data found, but no associated filetype info can be established"
    echo "Could be:"
    echo "    --- possible False Positive"
    echo "    --- possible embedded data, but incorrect password"
    echo "                 *****  no password supplied by default for OutGuess"
    echo "    --- possible embedded data, but with a different program"
    echo "                 *****  sometimes StegDetect things JSteg is Outguess and vice versa"
    echo "                 *****  might be worth scanning with each program separately" 
    echo "Result size: $SIZE (type: '`file $RESULT_FILE`')"
  fi
  rm $RESULT_FILE
}


echo
echo "<span class='text-center'>OUTGUESS-0.2</span><br><p><blocktext>"

/home/lukeslytalker/outguess/./outguess -r -k $PASS $FILE $TMP_FILE
check_result_file $TMP_FILE

echo "</blocktext></p>"

echo "<span class='text-center'>OUTGUESS-0.13</span><br><p><blocktext>"

/home/lukeslytalker/./outguess-0.13 -r -k $PASS $FILE $TMP_FILE
check_result_file $TMP_FILE

echo "</blocktext></p>"

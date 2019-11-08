#!/bin/bash

FILE=$1
TMP_FILE=/tmp/out

check_result_file() {
  RESULT_FILE=$1
  HINT=${2:""}
  if [ ! -f "$RESULT_FILE" ]; then
    echo "Nothing found."
    return
  fi

  SIZE=`stat -c %s "$RESULT_FILE"`

  if [ ! "`file $RESULT_FILE`" = "$RESULT_FILE: data" ] && [ $SIZE -ge 1 ]; then
    echo "Found something!!!"
    echo "Result size: $SIZE (type: '`file $RESULT_FILE`')"
    echo "<hr>"
    head -n 71 $RESULT_FILE
    echo "<hr>"
  elif [ $SIZE = 0 ]; then
    echo "Nothing found/no result"
  fi
  rm $RESULT_FILE
}

/home/lukeslytalker/./jsteg reveal $FILE $TMP_FILE
check_result_file $TMP_FILE


#!/bin/bash

FILE=$1
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
  elif [ $SIZE = 0 ]; then
    echo "Nothing found/no result"

  elif [ "`file $RESULT_FILE`" = "$RESULT_FILE: data" ] && [ $SIZE -ge 1 ]; then
    echo "Data found, but no associated filetype info can be established"
    echo "Could be:"
    echo "    --- possible False Positive"
    echo "    --- possible embedded data, but incorrect password"
    echo "                 *** no password supplied by default for OutGuess"
    echo "                 *** consider running an OutGuess Brute Force Password attack"
    echo "Result size: $SIZE (type: '`file $RESULT_FILE`')"
  fi
  rm $RESULT_FILE
}


echo
echo "#####################################"
echo "##########   StegoSaurus   ##########"
echo "##########   JPG Scanner   ##########"
echo "#####################################"
echo
echo "FILE TYPE: "
file $FILE

echo "IDENTIFY:"
identify -verbose $FILE

echo
echo "################################"
echo "########## stegdetect ##########"
echo "################################"

/home/lukeslytalker/stegdetect/./stegdetect -t jopifa  $FILE

echo
echo "##############################"
echo "########## outguess ##########"
echo "##############################"

/home/lukeslytalker/outguess/./outguess -r $FILE $TMP_FILE
check_result_file $TMP_FILE

echo
echo "###################################"
echo "########## outguess-0.13 ##########"
echo "###################################"

/home/lukeslytalker/./outguess-0.13 -r $FILE $TMP_FILE
check_result_file $TMP_FILE

echo
echo "###########################"
echo "########## jsteg ##########"
echo "###########################"

/home/lukeslytalker/./jsteg reveal $FILE $TMP_FILE
check_result_file $TMP_FILE

echo
echo "###########################"
echo "####### END OF SCAN #######"
echo "###########################"


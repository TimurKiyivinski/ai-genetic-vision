#!/bin/sh
TESTCOUNT=3

i=0
while [[ $i -lt $TESTCOUNT ]]
do
    echo "Running script number: $i"
    for usr in user/*.png;
    do
        BASELOG=$(basename $usr)-$i.log
        USERLOG=${BASELOG/".png"/""}
        echo "Logging user: $USERLOG"
        time python3 scan_number.py -f $usr > logging/$USERLOG
    done
    i=$(( i+1 ))
done

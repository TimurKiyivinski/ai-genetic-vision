#!/bin/sh
MUTCOUNT=4
for res in resources/*.png;
do
    python3 scan_number.py -f user/0.png -c $res -m $MUTCOUNT
done

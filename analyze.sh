#!/bin/sh
for x in resources/2*.png;
do
    python3 scan_number.py -f user/0.png -c $x -m 4
done

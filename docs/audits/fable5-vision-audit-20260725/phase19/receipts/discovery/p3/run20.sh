#!/bin/zsh
cd /tmp/p3
export P3_TGT=2.0
for M in 202510 202511 202512 202601; do python3 p3_walk.py $M > /tmp/p3/log20_$M.txt 2>&1 & done
wait
for M in 202602 202603 202604 202605; do python3 p3_walk.py $M > /tmp/p3/log20_$M.txt 2>&1 & done
wait
echo DONE20 > /tmp/p3/DONE20.txt

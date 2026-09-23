#!/bin/zsh
cd /tmp/p3
export P3_TGT=1.5
for M in 202510 202511 202512 202601; do python3 p3_walk.py $M > /tmp/p3/log15_$M.txt 2>&1 & done
wait
for M in 202602 202603 202604 202605; do python3 p3_walk.py $M > /tmp/p3/log15_$M.txt 2>&1 & done
wait
for M in 202510 202511 202512 202601 202602 202603 202604 202605; do mv /tmp/p3/P3_$M.npz /tmp/p3/P315_$M.npz; done
echo DONE15 > /tmp/p3/DONE15.txt

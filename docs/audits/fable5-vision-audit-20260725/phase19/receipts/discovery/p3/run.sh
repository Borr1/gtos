#!/bin/zsh
cd /tmp/p3
for M in 202510 202511 202512 202601; do
  python3 p3_walk.py $M > /tmp/p3/log_$M.txt 2>&1 &
done
wait
for M in 202602 202603 202604 202605; do
  python3 p3_walk.py $M > /tmp/p3/log_$M.txt 2>&1 &
done
wait
echo ALLDONE > /tmp/p3/DONE.txt

#!/bin/zsh
cd /tmp/p3
for S in XAGUSD EURUSD USDJPY; do python3 p3_ticks.py $S 202601 > /tmp/p3/tick_${S}_202601.log 2>&1; done
for S in XAUUSD XAGUSD EURUSD USDJPY; do python3 p3_ticks.py $S 202604 > /tmp/p3/tick_${S}_202604.log 2>&1; done
echo DONETICK > /tmp/p3/DONETICK.txt

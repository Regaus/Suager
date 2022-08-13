git pull
nohup python3 -u index.py > data/log.out 2>&1 </dev/null &
tail -f data/log.out
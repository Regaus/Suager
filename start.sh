git pull
nohup python3 -u index.py &>data/log.out &
tail -f data/log.out
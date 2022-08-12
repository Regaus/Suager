git pull
python3 -m pip install -U "git+https://github.com/Regaus/Regaus.py.git@stable#egg=regaus.py"
nohup python3 -u index.py &>data/log.out &
tail -f data/log.out
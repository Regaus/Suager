git pull
# Note to self: When I update the module, just run that command by myself
# python3.9 -m pip install -U "git+https://github.com/Regaus/Regaus.py.git@stable#egg=regaus.py"
nohup python3.9 -u index.py &>data/log.out &
tail -f data/log.out
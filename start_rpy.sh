sudo apt update
sudo apt upgrade -y
echo ""
git pull
echo ""
python3.11 -m pip install -U "git+https://github.com/Regaus/Regaus.py.git@stable#egg=regaus.py"
echo ""
nohup python3.11 -u index.py > data/log.out 2>&1 < /dev/null &
tail -f data/log.out
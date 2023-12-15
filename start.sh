sudo apt update
sudo apt upgrade -y
echo ""
git pull
echo ""
nohup python3.12 -u index.py > data/log.out 2>&1 < /dev/null &
tail -f data/log.out
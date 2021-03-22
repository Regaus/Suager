scp @vm:~/Suager/data/database.db /mnt/d/Regaus/OneDrive/2020/Bot_data/Database/$(date -Idate).db
python3 backup.py
./idiot.sh
from datetime import datetime

time = datetime.now().strftime("%Y-%m-%d")

command = f"scp @vm:~/Suager/data/database.db /mnt/d/Regaus/OneDrive/2020/Bot\\ data/Database/{time}.db"

print(command)

# eval $(python3 ~/database.py)
# can just be replaced with a sh command

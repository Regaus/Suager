import os
from datetime import date, timedelta


dirs = ["CobbleBot", "Suager"]
logs = ["cobble", "suager"]
today = date.today()
# yesterday = today - timedelta(days=1)
year = today.year
command = []

for i, log in enumerate(dirs):
    latest = f"{year}-01-01"
    path = f"/mnt/d/Regaus/OneDrive/2020/Bot data/{year}/{log}"
    path1 = path.replace("Bot data", "Bot\\ data")
    path2 = f"@vm:~/Suager/data/logs/{logs[i]}"
    for thing in sorted(os.listdir(path)):
        # if j == 0:
        #     continue
        # file = thing[0]
        # day = file.replace(path, "").replace("/", "").replace("\\", "")  # remove the path itself
        if "." in thing:
            continue
        latest = thing
        # print(latest)
    last = date.fromisoformat(latest)
    last += timedelta(days=1)
    while last < today:
        # print(f"{log} > Logs for {last.isoformat()} are not yet found")
        _date = last.isoformat()
        command.append(f"scp -r {path2}/{_date}/ {path1}/{_date}/")
        last += timedelta(days=1)

print("; ".join(command))

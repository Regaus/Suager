import asyncio
from math import ceil
from multiprocessing import cpu_count, Process, Array

from utils import time

enabled = False
run = False
last_command = time.now_ts()
pool = []
arr = Array("b", (False, False))


async def f(x, _arr):
    while True:
        _run = _arr[0]
        if _run and enabled:
            (x * x)
        else:
            # print(f"Loop: {enabled=} {_arr[0]=}")
            await asyncio.sleep(1)

        if _arr[1]:
            # print("Loop: Quitting...")
            quit(0)


def run_loop(x):
    asyncio.run(f(x, arr))


def setup():
    processes = ceil(cpu_count() / 2)
    for p in range(processes):
        process = Process(target=run_loop, args=(p,), name=f"Burner {p}")
        pool.append(process)
        process.start()
    # pool = Pool(processes)
    # pool.map(run_loop, range(processes))


async def cpu_burner():
    while True:
        if time.now_ts() - last_command > 120:
            global run
            run = True
        # if time.now_ts() - last_command > 30:
        #     arr[1] = True
        arr[0] = run
        # print(f"Burner: {enabled=} {run=} {arr[0]=} time={time.now_ts() - last_command:.2f}")
        await asyncio.sleep(1)

# logger.py

import csv
import os
from datetime import datetime
from settings import ACTIVER_LOGS_JOURNALIERS

def get_log_file_path():
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_folder = "logs"
    os.makedirs(log_folder, exist_ok=True)
    return os.path.join(log_folder, f"{today_str}.csv")

def init_log_file():
    if not ACTIVER_LOGS_JOURNALIERS:
        return

    log_file = get_log_file_path()
    if not os.path.exists(log_file):
        with open(log_file, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["datetime", "cycle", "pool", "score", "decision"])

def log_decision(pool_name, score, decision, cycle_id):
    if not ACTIVER_LOGS_JOURNALIERS:
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = get_log_file_path()

    with open(log_file, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([now, cycle_id, pool_name, score, decision])

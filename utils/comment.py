import csv
import random
import os

COMMENTS = []

def load_comments(csv_path=None):
    global COMMENTS
    if not csv_path:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(base_dir, "data", "comments.csv")

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        COMMENTS = [row for row in reader]

def get_comment(time, age, vehicle, weather):
    if not COMMENTS:
        load_comments()

    # 時間帯
    exact = [
        c for c in COMMENTS
        if c["time"] == time and
           c["age"] == age and
           c["vehicle"] == vehicle and
           c["weather"] == weather
    ]
    if exact:
        return random.choice(exact)["comment"]
    
    # any含む一致
    fallback = [
        c for c in COMMENTS
        if (c["time"] in (time, "any")) and
           (c["age"] in (age, "any")) and
           (c["vehicle"] in (vehicle, "any")) and
           (c["weather"] in (weather, "any"))
    ]
    if fallback:
        return random.choice(fallback)["comment"]

    # 最終ランダム
    return random.choice(COMMENTS)["comment"]

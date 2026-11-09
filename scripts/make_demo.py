#!/usr/bin/env python3
"""Buat data/threads.json berisi DATA CONTOH agar dashboard bisa dicoba sebelum token siap."""
import json
import math
import random
import time
from datetime import datetime, timezone
from pathlib import Path

random.seed(7)
OUT = Path(__file__).resolve().parent.parent / "data" / "threads.json"
WIB = 7 * 3600
now = int(time.time())
DAYS = 90

def activity(hour, dow):
    """Pola aktivitas audiens (jam WIB, dow 0=Senin)."""
    a = 0.15
    a += 0.9 * math.exp(-((hour - 7.5) ** 2) / 2)      # pagi berangkat kerja
    a += 1.0 * math.exp(-((hour - 12.5) ** 2) / 1.5)   # istirahat siang
    a += 1.6 * math.exp(-((hour - 20.5) ** 2) / 3.5)   # malam
    if hour < 5:
        a *= 0.25
    if dow >= 5:  # akhir pekan: pagi lebih siang, malam lebih panjang
        a = 0.2 + 1.2 * math.exp(-((hour - 10) ** 2) / 4) + 1.5 * math.exp(-((hour - 21) ** 2) / 4)
    return a

posts, reply_ts = [], []
samples = ["Tips produktif kerja dari rumah", "Thread: belajar PHP dari nol", "Opini soal AI di sekolah",
           "Behind the scene bikin dashboard", "Pertanyaan: tools favorit kalian?", "Rekap proyek minggu ini",
           "5 kesalahan pemula di WordPress", "Cerita lucu di kantor hari ini"]
for i in range(70):
    t = now - random.randint(0, DAYS * 86400)
    local = t + WIB
    hour = (local // 3600) % 24
    if hour < 6 and random.random() < 0.8:
        t += 8 * 3600
    local = t + WIB
    hour, dow = (local // 3600) % 24, ((local // 86400) + 3) % 7  # 1970-01-01 = Kamis
    act = activity(hour, dow)
    views = int(random.lognormvariate(math.log(400 * act + 120), 0.5))
    likes = int(views * random.uniform(0.03, 0.08))
    replies = int(views * random.uniform(0.005, 0.025)) + random.randint(0, 3)
    posts.append({
        "id": f"demo{i}", "ts": t, "text": random.choice(samples), "permalink": "",
        "type": "TEXT_POST", "views": views, "likes": likes, "replies": replies,
        "reposts": int(likes * random.uniform(0.05, 0.2)), "quotes": random.randint(0, 3),
        "shares": random.randint(0, 5),
    })
    # reply datang mengikuti pola aktivitas audiens dalam 48 jam setelah post
    for _ in range(replies):
        for _try in range(50):
            rt = t + int(random.expovariate(1 / 8000))
            if rt > now:
                continue
            lh = ((rt + WIB) // 3600) % 24
            ld = (((rt + WIB) // 86400) + 3) % 7
            if random.random() < activity(lh, ld) / 2.8:
                reply_ts.append(rt)
                break
# reply tambahan agar heatmap padat
for _ in range(1400):
    rt = now - random.randint(0, DAYS * 86400)
    lh = ((rt + WIB) // 3600) % 24
    ld = (((rt + WIB) // 86400) + 3) % 7
    if random.random() < activity(lh, ld) / 2.8:
        reply_ts.append(rt)

OUT.write_text(json.dumps({
    "demo": True,
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "lookback_days": DAYS,
    "account": {"username": "akun_contoh", "followers": 2480},
    "posts": sorted(posts, key=lambda x: x["ts"], reverse=True),
    "reply_ts": sorted(reply_ts),
}, separators=(",", ":")))
print(f"Demo: {len(posts)} post, {len(reply_ts)} reply")

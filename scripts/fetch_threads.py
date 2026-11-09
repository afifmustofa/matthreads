#!/usr/bin/env python3
"""
Ambil data akun Threads sendiri lewat Threads API, lalu simpan ke data/threads.json
untuk dibaca dashboard (index.html).

Yang disimpan:
  - daftar post (waktu posting + views, likes, replies, reposts, quotes, shares)
  - daftar timestamp reply dari audiens (TANPA username / isi reply)

Env:
  THREADS_ACCESS_TOKEN  wajib  - long-lived token Threads
  LOOKBACK_DAYS         opsional - default 90
  MAX_POSTS             opsional - default 300

Hanya pakai library standar Python (tidak perlu pip install).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://graph.threads.net/v1.0"
OUT = Path(__file__).resolve().parent.parent / "data" / "threads.json"

TOKEN = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
LOOKBACK_DAYS = int(os.environ.get("LOOKBACK_DAYS") or 90)
MAX_POSTS = int(os.environ.get("MAX_POSTS") or 300)


def api(path_or_url, params=None, retries=3):
    if path_or_url.startswith("http"):
        url = path_or_url
    else:
        q = dict(params or {})
        q["access_token"] = TOKEN
        url = f"{BASE}/{path_or_url.lstrip('/')}?{urllib.parse.urlencode(q)}"
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code in (429, 500, 502, 503) and attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} untuk {path_or_url}: {body[:300]}") from None
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(5)
                continue
            raise


def paginate(path, params, limit_items=None):
    data = api(path, params)
    items = list(data.get("data", []))
    while data.get("paging", {}).get("next") and (limit_items is None or len(items) < limit_items):
        data = api(data["paging"]["next"])
        items.extend(data.get("data", []))
    return items if limit_items is None else items[:limit_items]


def to_unix(ts):
    # format Threads: 2026-11-01T12:34:56+0000
    return int(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").timestamp())


def metric_value(item):
    if "total_value" in item:
        return item["total_value"].get("value", 0)
    vals = item.get("values") or [{}]
    return vals[0].get("value", 0)


def post_insights(media_id):
    for metrics in ("views,likes,replies,reposts,quotes,shares", "views,likes,replies,reposts,quotes"):
        try:
            data = api(f"{media_id}/insights", {"metric": metrics})
            return {m["name"]: metric_value(m) for m in data.get("data", [])}
        except RuntimeError as e:
            last = e
    print(f"  ! insights gagal untuk {media_id}: {last}", file=sys.stderr)
    return {}


def main():
    if not TOKEN:
        print("THREADS_ACCESS_TOKEN belum diisi - lewati (data demo tetap dipakai).")
        return 0

    me = api("me", {"fields": "id,username"})
    username = me.get("username", "")
    print(f"Akun: @{username}")

    followers = None
    try:
        ins = api("me/threads_insights", {"metric": "followers_count"})
        followers = metric_value(ins["data"][0]) if ins.get("data") else None
    except RuntimeError as e:
        print(f"  ! followers_count gagal: {e}", file=sys.stderr)

    since = int(time.time()) - LOOKBACK_DAYS * 86400
    raw_posts = paginate(
        "me/threads",
        {"fields": "id,text,timestamp,permalink,media_type", "since": since, "limit": 100},
        limit_items=MAX_POSTS,
    )
    raw_posts = [p for p in raw_posts if p.get("media_type") != "REPOST_FACADE" and p.get("timestamp")]
    print(f"Post ditemukan: {len(raw_posts)} (≤ {LOOKBACK_DAYS} hari terakhir)")

    posts, reply_ts = [], []
    for i, p in enumerate(raw_posts, 1):
        m = post_insights(p["id"])
        posts.append({
            "id": p["id"],
            "ts": to_unix(p["timestamp"]),
            "text": (p.get("text") or "")[:140],
            "permalink": p.get("permalink", ""),
            "type": p.get("media_type", ""),
            "views": m.get("views", 0),
            "likes": m.get("likes", 0),
            "replies": m.get("replies", 0),
            "reposts": m.get("reposts", 0),
            "quotes": m.get("quotes", 0),
            "shares": m.get("shares", 0),
        })
        if m.get("replies", 0) > 0:
            try:
                conv = paginate(f"{p['id']}/conversation",
                                {"fields": "id,timestamp,username", "reverse": "false", "limit": 100})
                for r in conv:
                    if r.get("username") != username and r.get("timestamp"):
                        reply_ts.append(to_unix(r["timestamp"]))
            except RuntimeError as e:
                print(f"  ! replies gagal untuk {p['id']}: {e}", file=sys.stderr)
        if i % 20 == 0:
            print(f"  … {i}/{len(raw_posts)} post diproses")

    out = {
        "demo": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lookback_days": LOOKBACK_DAYS,
        "account": {"username": username, "followers": followers},
        "posts": sorted(posts, key=lambda x: x["ts"], reverse=True),
        "reply_ts": sorted(reply_ts),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"Tersimpan: {OUT} — {len(posts)} post, {len(reply_ts)} reply audiens")
    return 0


if __name__ == "__main__":
    sys.exit(main())

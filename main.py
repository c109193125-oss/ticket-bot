import discord
from discord.ext import tasks
import requests
import asyncio
import os
import time


# ===== 讀取環境變數 =====
TOKEN = os.environ.get("TOKEN")

cid = os.environ.get("CHANNEL_ID")
CHANNEL_ID = int(cid) if cid and cid.strip().isdigit() else None

WATCH_LIST = [u.strip() for u in os.environ.get("WATCH_URLS", "").split(",") if u.strip()]

# 同一網址的通知冷卻時間（秒）避免狂洗
NOTIFY_COOLDOWN_SECONDS = 120
_last_notify_ts = {}  # url -> timestamp


# ===== Discord 設定 =====
intents = discord.Intents.default()
client = discord.Client(intents=intents)


def fetch_html(url: str) -> str:
    r = requests.get(
        url,
        timeout=12,
        headers={"User-Agent": "Mozilla/5.0 (compatible; TicketBot/1.0)"},
    )
    r.raise_for_status()
    return r.text


# ===== 檢查 KKTIX =====
def check_kktix(url: str) -> bool:
    try:
        t = fetch_html(url)

        # 售完 / 結束等字樣
        sold_out_keywords = ["已售完", "售完", "活動已結束", "停止售票"]
        if any(k in t for k in sold_out_keywords):
            return False

        # 可購買字樣
        ok_keywords = ["立即購買", "選擇張數", "Buy Tickets"]
        return any(k in t for k in ok_keywords)

    except Exception as e:
        print("KKTIX check failed:", e)
        return False


# ===== 檢查 拓元（強化版）=====
def check_tixcraft(url: str) -> bool:
    try:
        t = fetch_html(url)

        # 先排除明顯沒票/不可買的字樣（不同頁面會不一樣，先放常見的）
        sold_out_keywords = [
            "售完", "已售完", "目前沒有", "無票", "Sold Out", "已結束", "停止販售"
        ]
        if any(k in t for k in sold_out_keywords):
            return False

        # ✅ 可進行下一步/可購買的常見字樣
        ok_keywords = [
            "立即訂購", "立即購票", "立即購買",
            "下一步", "選擇區域", "選擇票區", "Select"
        ]
        if any(k in t for k in ok_keywords):
            return True

        return False

    except Exception as e:
        print("Tixcraft check failed:", e)
        return False


async def notify(url: str):
    # 冷卻避免洗版
    now = time.time()
    last = _last_notify_ts.get(url, 0)
    if now - last < NOTIFY_COOLDOWN_SECONDS:
        return
    _last_notify_ts[url] = now

    channel = client.get_channel(CHANNEL_ID) if CHANNEL_ID else None
    if channel:
        await channel.send(f"🔥 有票/有動靜了！\n{url}")
    else:
        print("Channel not found (CHANNEL_ID incorrect or bot lacks access).")


@tasks.loop(seconds=30)
async def monitor():
    if not WATCH_LIST:
        print("No watch urls yet... (set WATCH_URLS)")
        await asyncio.sleep(30)
        return

    for url in WATCH_LIST:
        ok = False

        if "kktix" in url:
            ok = check_kktix(url)
        elif "tixcraft" in url:
            ok = check_tixcraft(url)
        else:
            print("Unknown platform url, skipped:", url)
            continue

        if ok:
            print("Ticket activity detected:", url)
            await notify(url)
            await asyncio.sleep(10)


@client.event
async def on_ready():
    print("=== BOT READY ===")
    print("Logged in as:", client.user)
    print("CHANNEL_ID:", CHANNEL_ID)
    print("WATCH_URLS count:", len(WATCH_LIST))
    monitor.start()


if __name__ == "__main__":
    if not TOKEN:
        print("TOKEN missing! (set TOKEN in Railway Variables)")
        raise SystemExit(1)

    if CHANNEL_ID is None:
        print("CHANNEL_ID missing/invalid! (set CHANNEL_ID as digits in Railway Variables)")
        raise SystemExit(1)

    client.run(TOKEN)

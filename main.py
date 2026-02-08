import discord
from discord.ext import tasks
import requests
import asyncio
import os


# ===== 讀取環境變數（更穩定，不會因為 None 爆掉）=====
TOKEN = os.environ.get("TOKEN")

cid = os.environ.get("CHANNEL_ID")  # 可能是 None 或空字串
CHANNEL_ID = int(cid) if cid and cid.strip().isdigit() else None

WATCH_LIST = [
    u.strip()
    for u in os.environ.get("WATCH_URLS", "").split(",")
    if u.strip()
]


# ===== Discord 設定 =====
intents = discord.Intents.default()
client = discord.Client(intents=intents)


# ===== 檢查 KKTIX =====
def check_kktix(url: str) -> bool:
    try:
        r = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; TicketBot/1.0)"
            },
        )
        t = r.text

        # 常見售罄字樣
        if "已售完" in t:
            return False

        # 常見可購買字樣（可能因活動頁面不同而略有差異）
        if "立即購買" in t or "選擇張數" in t or "Buy Tickets" in t:
            return True

        return False
    except Exception as e:
        print("KKTIX check failed:", e)
        return False


# ===== 檢查 拓元 =====
def check_tixcraft(url: str) -> bool:
    try:
        r = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; TicketBot/1.0)"
            },
        )
        t = r.text

        if "售完" in t:
            return False

        if "立即訂購" in t or "立即購票" in t or "立即購買" in t:
            return True

        return False
    except Exception as e:
        print("Tixcraft check failed:", e)
        return False


# ===== 發通知 =====
async def notify(url: str):
    channel = client.get_channel(CHANNEL_ID) if CHANNEL_ID else None
    if channel:
        await channel.send(f"🔥 有票了！！！\n{url}")
    else:
        print("Channel not found (CHANNEL_ID incorrect or bot lacks access).")


# ===== 監控任務 =====
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
            # 不認得的平台就跳過（避免誤判）
            print("Unknown platform url, skipped:", url)
            continue

        if ok:
            print("Ticket found:", url)
            await notify(url)

            # 防止狂洗訊息（可自行調整）
            await asyncio.sleep(15)


# ===== Bot 上線事件 =====
@client.event
async def on_ready():
    print("=== BOT READY ===")
    print("Logged in as:", client.user)
    print("CHANNEL_ID:", CHANNEL_ID)
    print("WATCH_URLS count:", len(WATCH_LIST))
    monitor.start()


# ===== 啟動 =====
if __name__ == "__main__":
    if not TOKEN:
        print("TOKEN missing! (set TOKEN in Railway Variables)")
        raise SystemExit(1)

    if CHANNEL_ID is None:
        print("CHANNEL_ID missing/invalid! (set CHANNEL_ID as digits in Railway Variables)")
        raise SystemExit(1)

    client.run(TOKEN)

import discord
from discord.ext import tasks
import requests
import asyncio
import os


# ===== 讀取環境變數 =====
TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

# 用逗號分隔多個網址
WATCH_LIST = [
    u.strip()
    for u in os.environ.get("WATCH_URLS", "").split(",")
    if u.strip()
]


# ===== Discord 設定 =====
intents = discord.Intents.default()
client = discord.Client(intents=intents)


# ===== 檢查 KKTIX =====
def check_kktix(url):
    try:
        r = requests.get(url, timeout=10)
        t = r.text

        if "已售完" in t:
            return False

        if "立即購買" in t or "選擇張數" in t:
            return True

        return False
    except:
        return False


# ===== 檢查 拓元 =====
def check_tixcraft(url):
    try:
        r = requests.get(url, timeout=10)
        t = r.text

        if "售完" in t:
            return False

        if "立即訂購" in t or "立即購票" in t:
            return True

        return False
    except:
        return False


# ===== 發通知 =====
async def notify(url):
    channel = client.get_channel(CHANNEL_ID)

    if channel:
        await channel.send(f"🔥 有票了！！！\n{url}")
    else:
        print("Channel not found")


# ===== 監控任務 =====
@tasks.loop(seconds=30)
async def monitor():

    # 沒設定網址就先等等
    if not WATCH_LIST:
        print("No watch urls yet...")
        await asyncio.sleep(30)
        return

    for url in WATCH_LIST:

        ok = False

        if "kktix" in url:
            ok = check_kktix(url)

        elif "tixcraft" in url:
            ok = check_tixcraft(url)

        if ok:
            print("Ticket found:", url)
            await notify(url)

            # 防止狂洗訊息
            await asyncio.sleep(15)


# ===== Bot 上線事件 =====
@client.event
async def on_ready():
    print("=== BOT READY ===")
    print("Logged in as:", client.user)

    monitor.start()


# ===== 啟動 =====
if __name__ == "__main__":

    if not TOKEN:
        print("TOKEN missing!")
        exit(1)

    if not CHANNEL_ID:
        print("CHANNEL_ID missing!")
        exit(1)

    client.run(TOKEN)

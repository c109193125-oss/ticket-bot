import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
import asyncio
import os

TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID"))

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

WATCH_LIST = [
    # 之後把網址放這裡
]

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


async def notify(url):
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(f"🔥 有票了！\n{url}")


@tasks.loop(seconds=30)
async def monitor():
    for url in WATCH_LIST:

        ok = False

        if "kktix" in url:
            ok = check_kktix(url)
        elif "tixcraft" in url:
            ok = check_tixcraft(url)

        if ok:
            await notify(url)
            await asyncio.sleep(10)


@bot.event
async def on_ready():
    print("機器人上線！")
    monitor.start()


bot.run(TOKEN)

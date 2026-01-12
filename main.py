import os
import sys
import json
import asyncio
import platform
import requests
import websockets
from colorama import init, Fore
from keep_alive import keep_alive

init(autoreset=True)

# ================= CONFIG =================
status = "dnd"          # online / dnd / idle
custom_status = ""      # isi teks status custom
GATEWAY = "wss://gateway.discord.gg/?v=9&encoding=json"

# ================= TOKEN =================
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print(f"{Fore.RED}TOKEN belum diset di Environment!")
    sys.exit()

headers = {
    "Authorization": TOKEN,
    "Content-Type": "application/json"
}

# ================= VALIDATE =================
r = requests.get("https://canary.discordapp.com/api/v9/users/@me", headers=headers)
if r.status_code != 200:
    print(f"{Fore.RED}TOKEN INVALID!")
    sys.exit()

user = r.json()
username = user["username"]
userid = user["id"]

# ================= GATEWAY =================
async def onliner():
    async with websockets.connect(
        GATEWAY,
        max_size=None,
        max_queue=None,
        ping_interval=None
    ) as ws:

        # HELLO
        await ws.recv()

        # IDENTIFY
        auth = {
            "op": 2,
            "d": {
                "token": TOKEN,
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": "pc"
                },
                "presence": {
                    "status": status,
                    "afk": False
                }
            }
        }

        # CUSTOM STATUS
        cstatus = {
            "op": 3,
            "d": {
                "since": 0,
                "activities": [{
                    "type": 4,
                    "state": custom_status,
                    "name": "Custom Status",
                    "id": "custom"
                }],
                "status": status,
                "afk": False
            }
        }

        await ws.send(json.dumps(auth))
        await ws.send(json.dumps(cstatus))

        # DIAM, JANGAN KIRIM APA-APA LAGI
        while True:
            await asyncio.sleep(60)

# ================= RUN =================
async def main():
    os.system("cls" if platform.system() == "Windows" else "clear")
    print(
        f"{Fore.GREEN}[+] Logged in as "
        f"{Fore.CYAN}{username}{Fore.WHITE} ({userid})"
    )

    while True:
        try:
            await onliner()
        except Exception as e:
            print(f"{Fore.YELLOW}Reconnect: {e}")
            await asyncio.sleep(10)

keep_alive()
asyncio.run(main())

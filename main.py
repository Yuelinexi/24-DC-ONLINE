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

status = "dnd"          # online / dnd / idle
custom_status = ""      # custom status text

# ================== TOKEN ==================
usertoken = os.getenv("TOKEN")
if not usertoken:
    print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] TOKEN belum diset di Environment.")
    sys.exit()

headers = {
    "Authorization": usertoken,
    "Content-Type": "application/json"
}

validate = requests.get(
    "https://canary.discordapp.com/api/v9/users/@me",
    headers=headers
)
if validate.status_code != 200:
    print(f"{Fore.WHITE}[{Fore.RED}-{Fore.WHITE}] Token INVALID.")
    sys.exit()

userinfo = validate.json()
username = userinfo["username"]
userid = userinfo["id"]

# ================== SAFE SEND ==================
async def safe_send(ws, data):
    payload = json.dumps(data)
    if len(payload) > 900_000:
        print("⚠ Payload terlalu besar, dilewati")
        return
    await ws.send(payload)

# ================== HEARTBEAT ==================
async def heartbeat_loop(ws, interval):
    while True:
        await asyncio.sleep(interval / 1000)
        await safe_send(ws, {"op": 1, "d": None})

# ================== GATEWAY ==================
async def onliner(token, status):
    async with websockets.connect(
        "wss://gateway.discord.gg/?v=9&encoding=json",
        max_size=2**20
    ) as ws:

        hello = json.loads(await ws.recv())
        heartbeat_interval = hello["d"]["heartbeat_interval"]

        auth = {
            "op": 2,
            "d": {
                "token": token,
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

        await safe_send(ws, auth)
        await safe_send(ws, cstatus)

        asyncio.create_task(heartbeat_loop(ws, heartbeat_interval))
        await asyncio.Future()  # stay connected

# ================== RUN ==================
async def run_onliner():
    os.system("cls" if platform.system() == "Windows" else "clear")
    print(
        f"{Fore.WHITE}[{Fore.LIGHTGREEN_EX}+{Fore.WHITE}] "
        f"Logged in as {Fore.LIGHTBLUE_EX}{username}{Fore.WHITE} ({userid})"
    )
    while True:
        try:
            await onliner(usertoken, status)
        except Exception as e:
            print("Reconnect:", e)
            await asyncio.sleep(5)

keep_alive()
asyncio.run(run_onliner())

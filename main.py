import os
import json
import asyncio
import requests
import websockets
from keep_alive import keep_alive

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("TOKEN kosong")
    exit()

headers = {
    "Authorization": TOKEN,
    "Content-Type": "application/json"
}

# VALIDASI TOKEN
r = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
if r.status_code != 200:
    print("TOKEN INVALID")
    exit()

user = r.json()
print(f"[+] Logged in as {user['username']}#{user['discriminator']}")

STATUS = "online"  # online / dnd / idle
CUSTOM_STATUS = "online 24/7"

async def heartbeat(ws, interval):
    while True:
        await asyncio.sleep(interval)
        await ws.send(json.dumps({"op": 1, "d": None}))

async def connect():
    async with websockets.connect(
        "wss://gateway.discord.gg/?v=9&encoding=json",
        max_size=2**20
    ) as ws:

        hello = json.loads(await ws.recv())
        interval = hello["d"]["heartbeat_interval"] / 1000

        identify = {
            "op": 2,
            "d": {
                "token": TOKEN,
                "intents": 0,
                "properties": {
                    "$os": "linux",
                    "$browser": "chrome",
                    "$device": "pc"
                },
                "presence": {
                    "status": STATUS,
                    "since": 0,
                    "activities": [{
                        "name": "Custom Status",
                        "type": 4,
                        "state": CUSTOM_STATUS
                    }],
                    "afk": False
                }
            }
        }

        await ws.send(json.dumps(identify))

        asyncio.create_task(heartbeat(ws, interval))

        while True:
            await ws.recv()  # keep connection alive

async def main():
    while True:
        try:
            await connect()
        except Exception as e:
            print("Reconnect:", e)
            await asyncio.sleep(5)

keep_alive()
asyncio.run(main())

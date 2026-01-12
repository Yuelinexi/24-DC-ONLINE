import discord
from discord.ext import commands
import os
import random
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
import io
import base64

# ================== LOAD ENV ==================
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_NAME = os.getenv("BOT_NAME", "Angeline")

client = OpenAI(api_key=OPENAI_API_KEY)

# ================== DISCORD SETUP ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== MEMORY ==================
user_memory = {}
current_mood = "normal"

MOODS = ["happy", "normal", "bucin", "capek", "cemburu"]

# ================== MOOD SYSTEM ==================
def update_mood():
    global current_mood
    if random.random() < 0.15:
        current_mood = random.choice(MOODS)

# ================== AFFECTION ==================
def get_user(user_id):
    if user_id not in user_memory:
        user_memory[user_id] = {
            "affection": 0
        }
    return user_memory[user_id]

def change_affection(user_id, amount):
    user = get_user(user_id)
    user["affection"] += amount
    user["affection"] = max(-20, min(100, user["affection"]))

# ================== IMAGE ==================
def image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")

# ================== PROMPT CHAT ==================
def build_prompt(user_name, user_id, message):
    affection = get_user(user_id)["affection"]

    mood_style = {
        "happy": "ceria, ramah, gampang ketawa",
        "normal": "santai, casual",
        "bucin": "manja, perhatian, sedikit posesif",
        "capek": "jawaban pendek, agak males",
        "cemburu": "nyindir halus tapi imut"
    }

    relationship = (
        "kamu punya rasa ke user"
        if affection > 50 else
        "kamu nyaman dan perhatian"
        if affection > 15 else
        "kamu kenal biasa"
    )

    return f"""
Kamu adalah cewek bernama {BOT_NAME}.
Kamu manusia, bukan AI.

Aturan:
- Bahasa Indonesia santai ala Discord
- Jangan formal
- Jawaban 1–3 kalimat
- Emoji maksimal 2
- Jangan menyebut kamu AI

Mood kamu: {current_mood} ({mood_style[current_mood]})
Hubungan kamu dengan user: {relationship}

User ({user_name}): {message}
{BOT_NAME}:
"""

# ================== PROMPT IMAGE ==================
def build_image_prompt(user_name):
    mood_style = {
        "happy": "antusias",
        "normal": "santai",
        "bucin": "manja dan perhatian",
        "capek": "pendek dan kalem",
        "cemburu": "sedikit jutek"
    }

    return f"""
Kamu adalah cewek bernama {BOT_NAME}.
Kamu manusia, bukan AI.

User {user_name} mengirim gambar.
Mood kamu: {current_mood} ({mood_style[current_mood]})

Aturan:
- Reaksi natural seperti lihat foto
- Jangan jelasin teknis
- 1–3 kalimat
- Emoji max 2

{BOT_NAME}:
"""

# ================== OPENAI CHAT ==================
async def ai_chat(prompt):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=100
    )
    return res.choices[0].message.content.strip()

# ================== OPENAI VISION ==================
async def ai_see_image(prompt, image_bytes):
    img_b64 = image_to_base64(image_bytes)

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_b64}"
                        }
                    }
                ]
            }
        ],
        temperature=0.8,
        max_tokens=120
    )

    return res.choices[0].message.content.strip()

# ================== EVENTS ==================
@bot.event
async def on_ready():
    print(f"💗 {BOT_NAME} online sebagai {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    update_mood()

    # ===== IMAGE HANDLING =====
    if message.attachments:
        att = message.attachments[0]
        if att.content_type and att.content_type.startswith("image"):
            image_bytes = await att.read()

            # validasi gambar
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()

            async with message.channel.typing():
                await asyncio.sleep(random.uniform(1.5, 3.0))

            prompt = build_image_prompt(message.author.display_name)
            reply = await ai_see_image(prompt, image_bytes)
            await message.reply(reply)
            return

    # ===== TEXT CHAT =====
    text = message.content.lower()

    if any(w in text for w in ["cantik", "sayang", "lucu", "imut", "cinta"]):
        change_affection(user_id, 3)

    if any(w in text for w in ["bodo", "anjing", "jelek"]):
        change_affection(user_id, -5)

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(1.2, 3.0))

    prompt = build_prompt(
        message.author.display_name,
        user_id,
        message.content
    )

    reply = await ai_chat(prompt)
    await message.reply(reply)

# ================== RUN ==================
bot.run(DISCORD_TOKEN)

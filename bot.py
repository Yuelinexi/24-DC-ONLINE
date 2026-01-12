import discord
from discord.ext import commands
import os
import random
import asyncio
from dotenv import load_dotenv
from PIL import Image
import io
import google.generativeai as genai

# ================== LOAD ENV ==================
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BOT_NAME = os.getenv("BOT_NAME", "Angeline")

# ================== GEMINI ==================
genai.configure(api_key=GEMINI_API_KEY)

chat_model = genai.GenerativeModel("gemini-1.5-flash")
vision_model = genai.GenerativeModel("gemini-1.5-flash")

# ================== DISCORD ==================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== MEMORY ==================
user_memory = {}
current_mood = "normal"
MOODS = ["happy", "normal", "bucin", "capek", "cemburu"]

# ================== MOOD ==================
def update_mood():
    global current_mood
    if random.random() < 0.15:
        current_mood = random.choice(MOODS)

# ================== AFFECTION ==================
def get_user(user_id):
    if user_id not in user_memory:
        user_memory[user_id] = {"affection": 0}
    return user_memory[user_id]

def change_affection(user_id, amount):
    u = get_user(user_id)
    u["affection"] = max(-20, min(100, u["affection"] + amount))

# ================== PROMPT CHAT ==================
def build_prompt(user_name, user_id, message):
    affection = get_user(user_id)["affection"]

    mood_style = {
        "happy": "ceria, ramah",
        "normal": "santai, casual",
        "bucin": "manja, perhatian",
        "capek": "jawaban pendek",
        "cemburu": "sedikit jutek tapi imut"
    }

    relationship = (
        "kamu punya rasa ke user"
        if affection > 50 else
        "kamu nyaman ngobrol"
        if affection > 15 else
        "kamu kenal biasa"
    )

    return f"""
Kamu adalah cewek bernama {BOT_NAME}.
Kamu manusia, bukan AI.

Gaya:
- Bahasa Indonesia santai ala Discord
- Jangan formal
- Jawaban 1–3 kalimat
- Emoji maksimal 2
- Jangan bilang kamu AI

Mood: {current_mood} ({mood_style[current_mood]})
Hubungan: {relationship}

User ({user_name}): {message}
{BOT_NAME}:
"""

# ================== PROMPT IMAGE ==================
def build_image_prompt(user_name):
    return f"""
Kamu adalah cewek bernama {BOT_NAME}.
Kamu manusia, bukan AI.

User {user_name} mengirim gambar.
Mood kamu: {current_mood}

Reaksi natural:
- 1–3 kalimat
- Emoji max 2
- Jangan jelasin teknis

{BOT_NAME}:
"""

# ================== GEMINI CHAT ==================
async def ai_chat(prompt):
    try:
        res = chat_model.generate_content(prompt)
        return res.text.strip()
    except Exception:
        return "eh maaf ya… aku lagi bengong dikit 😅"

# ================== GEMINI VISION ==================
async def ai_see_image(prompt, image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        res = vision_model.generate_content([prompt, img])
        return res.text.strip()
    except Exception:
        return "aku liat fotonya sih… tapi kepikiran hal lain 🙃"

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

    # ===== IMAGE =====
    if message.attachments:
        att = message.attachments[0]
        if att.content_type and att.content_type.startswith("image"):
            image_bytes = await att.read()

            async with message.channel.typing():
                await asyncio.sleep(random.uniform(1.5, 3.0))

            prompt = build_image_prompt(message.author.display_name)
            reply = await ai_see_image(prompt, image_bytes)
            await message.reply(reply)
            return

    # ===== TEXT =====
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

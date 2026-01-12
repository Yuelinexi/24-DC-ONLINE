import discord
from discord.ext import commands
import os, random, asyncio, io
from dotenv import load_dotenv
from PIL import Image
from google import genai

# ================= ENV =================
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BOT_NAME = os.getenv("BOT_NAME", "Angeline")

# ================= GEMINI =================
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "models/gemini-1.0-pro"  # VALID & STABIL

# ================= DISCORD =================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= STATE =================
user_memory = {}
current_mood = "normal"
MOODS = ["happy", "normal", "bucin", "capek", "cemburu"]

# ================= UTILS =================
def update_mood():
    global current_mood
    if random.random() < 0.15:
        current_mood = random.choice(MOODS)

def get_user(uid):
    if uid not in user_memory:
        user_memory[uid] = {"affection": 0}
    return user_memory[uid]

def build_prompt(username, uid, msg):
    aff = get_user(uid)["affection"]
    relation = "punya rasa ke user" if aff > 40 else "teman ngobrol"

    return f"""
Kamu adalah cewek bernama {BOT_NAME}, manusia (bukan AI).
Gaya chat Discord, santai, natural, 1–3 kalimat, emoji max 2.
Mood sekarang: {current_mood}
Hubungan dengan user: {relation}

User ({username}): {msg}
{BOT_NAME}:
"""

# ================= GEMINI =================
async def gemini_text(prompt):
    try:
        res = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        if not res.text:
            return None
        return res.text.strip()
    except Exception as e:
        print("Gemini error:", e)
        return None  # PENTING: JANGAN BALAS APA-APA

async def gemini_image(prompt, image_bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        res = client.models.generate_content(
            model=MODEL,
            contents=[prompt, img]
        )
        if not res.text:
            return None
        return res.text.strip()
    except Exception as e:
        print("Gemini image error:", e)
        return None

# ================= EVENTS =================
@bot.event
async def on_ready():
    print(f"💗 {BOT_NAME} online sebagai {bot.user}")

@bot.event
async def on_message(message):
    # ===== BLOCK TOTAL =====
    if message.author.id == bot.user.id:
        return

    # ===== HANYA JAWAB JIKA DI-MENTION =====
    if bot.user not in message.mentions:
        return

    # ===== BERSIHKAN MENTION =====
    clean = (
        message.content
        .replace(f"<@{bot.user.id}>", "")
        .replace(f"<@!{bot.user.id}>", "")
        .strip()
    )
    if not clean:
        return

    update_mood()
    uid = message.author.id

    # ===== IMAGE =====
    if message.attachments:
        att = message.attachments[0]
        if att.content_type and att.content_type.startswith("image"):
            img = await att.read()
            prompt = f"{BOT_NAME} bereaksi ke gambar user dengan gaya cewek natural."
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(1.5, 2.5))
            reply = await gemini_image(prompt, img)
            if reply:
                await message.reply(reply)
            return

    # ===== TEXT =====
    text_lower = clean.lower()
    if any(w in text_lower for w in ["cantik", "sayang", "imut", "lucu"]):
        get_user(uid)["affection"] += 2

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(1.2, 2.2))

    prompt = build_prompt(
        message.author.display_name,
        uid,
        clean
    )

    reply = await gemini_text(prompt)
    if not reply:
        return  # DIAM TOTAL JIKA GEMINI ERROR

    await message.reply(reply)

# ================= RUN =================
bot.run(DISCORD_TOKEN)

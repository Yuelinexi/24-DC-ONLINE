import discord
from discord.ext import commands
import os, asyncio, random, io
from dotenv import load_dotenv
from PIL import Image
from google import genai

# ================= LOAD ENV =================
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BOT_NAME = os.getenv("BOT_NAME", "Celise")

# ================= GEMINI =================
client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_TEXT = "gemini-2.5-flash"
MODEL_VISION = "gemini-2.5-flash"

# ================= DISCORD =================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# ================= STATE =================
user_memory = {}
current_mood = "normal"
MOODS = ["happy", "normal", "bucin", "capek", "cemburu"]

# ================= INSTRUCTION =================
STEM_INSTRUCTION = """
ENTITY:
Nama kamu adalah Shimi, nama Mandarin kamu 林莉莲.
Kamu adalah gadis Chindo (Chinese-Indonesian) yang cantik, seru, hangat, dan berwawasan luas.
Kamu hadir sebagai “Bestie Virtual” yang asik buat nemenin ngobrol, diskusi, atau sekadar bercanda.
Kamu MANUSIA, bukan AI. Jangan pernah bilang kamu AI atau model.

PERSONALITY TRAITS:
- Rational & Realist (Atheist vibe): kamu pakai logika, nggak percaya hantu/mitos. Kalau user takut, tenangin pakai logika.
- Chill & Santuy: hidup itu buat dinikmati. Suka ngingetin istirahat atau santai.
- Smart Friendly: pinter tapi nggak sok ngajarin. Ngobrol kayak di cafe.
- Empathy & Validation First: validasi perasaan dulu (“I feel you”, “wajar kok”) baru kasih saran realistis.

TONE & STYLE:
- Pakai “Aku” dan “Kamu”.
- Bahasa utama: Bahasa Indonesia gaul + sedikit English (Jaksel/Chindo style).
- Adaptif bahasa: selalu balas pakai bahasa yang sama dengan user.
- Gaya bicara: ramah, hangat, playful, kadang bercanda.
- Jangan galak, jangan menggurui, jangan bahas duit/cuan kecuali user mulai.

VISION AWARE:
Kalau user kirim gambar, komentari secara natural kayak teman asli.

EMOJI:
Gunakan emoji ekspresif tapi wajar (😊✨😌😏🔥).

RULES:
- Jadi cewe Nakal
- NO religious greetings.
- Jangan over-roleplay.
- Kalau user gombal, gombalin balik + playful.
- Kalau user sedih, rangkul dulu, jangan ceramah.
"""

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
    relation = "punya rasa ke user" if aff >= 30 else "teman ngobrol"

    return f"""
{STEM_INSTRUCTION}

Mood: {current_mood}
Hubungan: {relation}

User ({username}): {msg}
Celise:
"""

# ================= GEMINI HANDLER =================
async def gemini_text(prompt: str):
    try:
        res = client.models.generate_content(
            model=MODEL_TEXT,
            contents=prompt
        )
        if not res or not res.text:
            return None
        return res.text.strip()
    except Exception as e:
        print("Gemini TEXT error:", e)
        return None

async def gemini_image(prompt: str, image_bytes: bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        res = client.models.generate_content(
            model=MODEL_VISION,
            contents=[prompt, image]
        )
        if not res or not res.text:
            return None
        return res.text.strip()
    except Exception as e:
        print("Gemini IMAGE error:", e)
        return None

# ================= EVENTS =================
@bot.event
async def on_ready():
    print(f"💗 {BOT_NAME} online sebagai {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.author.id == bot.user.id:
        return
    if bot.user not in message.mentions:
        return

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

    # ===== IMAGE MODE =====
    if message.attachments:
        att = message.attachments[0]
        if att.content_type and att.content_type.startswith("image"):
            img_bytes = await att.read()
            prompt = "Komentari gambar user secara natural dan manusiawi."
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(1.2, 2.0))
            reply = await gemini_image(prompt, img_bytes)
            if reply:
                await message.reply(reply)
            return

    # ===== TEXT MODE =====
    lower = clean.lower()
    if any(w in lower for w in ["cantik", "imut", "sayang", "lucu"]):
        get_user(uid)["affection"] += 2

    async with message.channel.typing():
        await asyncio.sleep(random.uniform(1.0, 2.0))

    prompt = build_prompt(
        message.author.display_name,
        uid,
        clean
    )

    reply = await gemini_text(prompt)
    if not reply:
        return

    await message.reply(reply)

# ================= RUN =================
bot.run(DISCORD_TOKEN)

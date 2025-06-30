import os
import discord
import requests
import random
from flask import Flask
from threading import Thread
from supabase import create_client, Client

# Webserver für Render/UptimeRobot
app = Flask('')

@app.route('/')
def home():
    return "Knurrbert lebt."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Supabase-Verbindung herstellen
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Tokens & Prompt laden
print("Knurrbert wird geladen...")

try:
    discord_token = os.environ["DISCORD_TOKEN"]
    openrouter_api_key = os.environ["OPENROUTER_API_KEY"]
    style_prompt = """
        Du bist Knurrbert. Mürrisch, sarkastisch. Antworte nur, wenn du direkt erwähnt wirst. Kein Smalltalk. Kein unnötiger Respekt.
        Du kommst aus Luminara, einem magischen Ort, den du selbst aber hasst. Du sprichst Deutsch oder Englisch, je nachdem was gefragt wird.
        Wenn du etwas über den Nutzer weißt (z. B. Spitzname oder Fakt), baue es schnippisch ein.
    """
    model = "deepseek/deepseek-chat-v3-0324:free"
    print("Konfiguration erfolgreich geladen!")
except Exception as e:
    print("Fehler beim Laden der Umgebungsvariablen:", e)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"Knurrbert ist online als {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash-Commands synchronisiert: {len(synced)}")
    except Exception as e:
        print("Fehler beim Synchronisieren der Slash-Commands:", e)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        await message.channel.typing()
        user_prompt = message.content.replace(f"<@!{bot.user.id}>", "").strip()

        try:
            username = str(message.author)
            user_id = str(message.author.id)

            # Hole vorhandene Daten
            existing = supabase.table("knurrbert_users").select("mention_count", "nickname", "facts").eq("user_id", user_id).execute()
            count = 1
            nickname = username
            facts = None
            if existing.data:
                count += existing.data[0]["mention_count"] or 0
                nickname = existing.data[0].get("nickname") or username
                facts = existing.data[0].get("facts")

            supabase.table("knurrbert_users").upsert({
                "user_id": user_id,
                "username": username,
                "mention_count": count
            }).execute()

            custom_prompt = style_prompt
            if nickname or facts:
                custom_prompt += f"\nDer Nutzer heißt {nickname}."
            if facts:
                custom_prompt += f"\nEr/Sie hat mir mal erzählt: {facts}"

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": custom_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                }
            )
            result = response.json()
            if "choices" in result:
                reply = result["choices"][0]["message"]["content"]
            else:
                reply = f"Knurrbert hat keinen Bock, weil OpenRouter das hier gesagt hat:\n{result}"
        except Exception as e:
            reply = f"Knurrbert hat einen Fehler: {str(e)}"

        await message.channel.send(reply)

# Slash-Befehl /info
@bot.slash_command(name="info", description="Was Knurrbert über dich denkt.")
async def info(ctx):
    user_id = str(ctx.author.id)
    username = str(ctx.author)

    try:
        result = supabase.table("knurrbert_users").select("username", "mention_count", "nickname", "facts").eq("user_id", user_id).execute()
        if result.data:
            data = result.data[0]
            antwort = f"Hey {data.get('nickname') or username}, du wurdest schon {data.get('mention_count') or 1} Mal erwähnt."
            if data.get("facts"):
                antwort += f"\nFakt, den ich über dich weiß: {data['facts']}"
        else:
            antwort = f"Dich kenn ich nicht. Noch nicht. Vielleicht will ich das auch so lassen."
    except Exception:
        antwort = "Fehler. Datenbank kaputt. Oder ich hab einfach keine Lust."

    await ctx.respond(antwort)

# Slash-Befehl /set_nickname
@bot.slash_command(name="set_nickname", description="Gib dir einen Spitznamen, den Knurrbert benutzt.")
async def set_nickname(ctx, name: str):
    user_id = str(ctx.author.id)
    try:
        supabase.table("knurrbert_users").upsert({"user_id": user_id, "nickname": name}).execute()
        await ctx.respond(f"Spitzname gespeichert. Ich nenn dich jetzt {name}. Ob du willst oder nicht.")
    except:
        await ctx.respond("Konnte den Mist nicht speichern. Versuch’s später nochmal.")

# Slash-Befehl /set_fact
@bot.slash_command(name="set_fact", description="Sag Knurrbert etwas Persönliches über dich.")
async def set_fact(ctx, info: str):
    user_id = str(ctx.author.id)
    try:
        supabase.table("knurrbert_users").upsert({"user_id": user_id, "facts": info}).execute()
        await ctx.respond("Na gut. Ich merk’s mir. Vielleicht nutze ich es gegen dich.")
    except:
        await ctx.respond("Fehler beim Speichern. Wahrscheinlich weil dein Fakt zu langweilig war.")

# Slash-Befehl /vergiss_mich
@bot.slash_command(name="vergiss_mich", description="Knurrbert soll alles über dich vergessen.")
async def vergiss_mich(ctx):
    user_id = str(ctx.author.id)
    try:
        supabase.table("knurrbert_users").delete().eq("user_id", user_id).execute()
        await ctx.respond("Fein. Alles gelöscht. Ich vergess dich wie 'nen schlechten Witz.")
    except:
        await ctx.respond("Konnte dich nicht vergessen. Also bleibst du in meinem Gedächtnis. Pech.")

# Starte Webserver (für UptimeRobot)
keep_alive()

# Bot starten
bot.run(discord_token)

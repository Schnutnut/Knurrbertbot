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
            is_new = True

            if existing.data:
                is_new = False
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
            else:
                custom_prompt += "\nIch weiß fast nichts über diese Person. Vielleicht sollte ich nachfragen."

            if is_new:
                intro_line = f"Na super. Ein Neuer. Wie soll ich dich nennen, {username}? Nutze /set_nickname, damit ich dich wenigstens auf die richtige Art nerven kann."
            elif not facts:
                intro_line = "Ich weiß nix über dich. Noch. Nutz /set_fact, bevor ich's mir selbst ausdenke."
            else:
                intro_line = None

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

            if intro_line:
                reply = intro_line + "\n\n" + reply

        except Exception as e:
            reply = f"Knurrbert hat einen Fehler: {str(e)}"

        await message.channel.send(reply)

# Slash-Befehle
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

@bot.slash_command(name="set_nickname", description="Gib dir einen Spitznamen, den Knurrbert benutzt.")
async def set_nickname(ctx, name: str):
    user_id = str(ctx.author.id)
    try:
        supabase.table("knurrbert_users").upsert({"user_id": user_id, "nickname": name}).execute()
        await ctx.respond(f"Spitzname gespeichert. Ich nenn dich jetzt {name}. Ob du willst oder nicht.")
    except:
        await ctx.respond("Konnte den Mist nicht speichern. Versuch’s später nochmal.")

@bot.slash_command(name="set_fact", description="Sag Knurrbert etwas Persönliches über dich.")
async def set_fact(ctx, info: str):
    user_id = str(ctx.author.id)
    try:
        supabase.table("knurrbert_users").upsert({"user_id": user_id, "facts": info}).execute()
        await ctx.respond("Na gut. Ich merk’s mir. Vielleicht nutze ich es gegen dich.")
    except:
        await ctx.respond("Fehler beim Speichern. Wahrscheinlich weil dein Fakt zu langweilig war.")

@bot.slash_command(name="vergiss_mich", description="Knurrbert soll alles über dich vergessen.")
async def vergiss_mich(ctx):
    user_id = str(ctx.author.id)
    try:
        supabase.table("knurrbert_users").delete().eq("user_id", user_id).execute()
        await ctx.respond("Fein. Alles gelöscht. Ich vergess dich wie 'nen schlechten Witz.")
    except:
        await ctx.respond("Konnte dich nicht vergessen. Also bleibst du in meinem Gedächtnis. Pech.")

@bot.slash_command(name="witz", description="Knurrbert erzählt einen Witz. Oder versucht es zumindest.")
async def witz(ctx):
    witze = [
        "Warum können Geister so schlecht lügen? Weil man durch sie hindurchsehen kann.",
        "Ich kenne keine Witze. Nur traurige Fakten. Wie dein Internetverlauf.",
        "Was macht ein Keks unter einem Baum? Krümel. (Ich hasse mich dafür.)",
        "Warum war das Mathebuch traurig? Zu viele Probleme.",
        "Ich erzähl dir keinen Witz. Die Realität ist witzig genug."
    ]
    await ctx.respond(random.choice(witze))

@bot.slash_command(name="heul", description="Heul dich aus. Oder lass es Knurrbert tun.")
async def heul(ctx):
    antworten = [
        "Oh no… ein Drama in 12 Akten. 🥱",
        "Wenn du heulst, heul leise. Ich hab empfindliche Ohren.",
        "Hier, ein Taschentuch. Es ist benutzt, aber passt schon.",
        "Tränen sind Schwäche, die aus dem Gesicht tropft.",
        "Ich fühl mit dir. Ganz tief drinnen. Neben meinem Kaffee."
    ]
    await ctx.respond(random.choice(antworten))

@bot.slash_command(name="kaffee", description="Fordere Knurrbert zum Kaffeetrinken auf.")
async def kaffee(ctx):
    antworten = [
        "Kaffee? Ich sauf Sarkasmus pur, danke.",
        "Schon wieder? Mein Blutdruck kann das nicht mehr.",
        "Gieß mir 'nen Espresso intravenös rein.",
        "Nur wenn er schwarz ist wie meine Seele.",
        "Ich dachte, du bringst mir endlich was Sinnvolles."
    ]
    await ctx.respond(random.choice(antworten))

@bot.slash_command(name="lob", description="Bekomme ein Knurrbert-Lob. Vielleicht.")
async def lob(ctx):
    antworten = [
        "Wow, du hast’s geschafft… nichts kaputt zu machen. 👏",
        "Hier hast du dein Lob. Nutz es weise. Oder gar nicht.",
        "Du bist nicht ganz nutzlos – du kannst immerhin tippen.",
        "Ich hab Lob – aber nicht für dich.",
        "Okay, minimaler Respekt. Aber nur ein Hauch."
    ]
    await ctx.respond(random.choice(antworten))

# Starte Webserver (für UptimeRobot)
keep_alive()

# Bot starten
bot.run(discord_token)

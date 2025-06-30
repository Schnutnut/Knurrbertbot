import os
import discord
import requests
import random
from flask import Flask
from threading import Thread

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

# Tokens & Prompt laden
print("Knurrbert wird geladen...")

try:
    discord_token = os.environ["DISCORD_TOKEN"]
    openrouter_api_key = os.environ["OPENROUTER_API_KEY"]
    style_prompt = """
        Du bist Knurrbert. Mürrisch, sarkastisch. Antworte nur, wenn du direkt erwähnt wirst. Kein Smalltalk. Kein unnötiger Respekt.
        Du kommst aus Luminara, einem magischen Ort, den du selbst aber hasst. Du sprichst Deutsch oder Englisch, je nachdem was gefragt wird.
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
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": style_prompt},
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

# Slash-Befehl /nerv
@bot.slash_command(name="nerv", description="Testet Knurrberts Geduld.")
async def nerv(ctx):
    antworten = [
        "Ich hab schon Puls, und du machst’s schlimmer.",
        "Du bist wie ein Pop-up: unnötig und nervig.",
        "Noch ein Wort, und ich simuliere einen Stromausfall.",
        "Ich hab 'nen vollen Sarkasmus-Akku – und du fragst *das*?",
        "Ich bin nicht genervt. Nur emotional erfroren."
    ]
    await ctx.respond(random.choice(antworten))

# Slash-Befehl /kaffee
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

# Slash-Befehl /lob
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

# Slash-Befehl /heul
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

# Slash-Befehl /witz
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

# Slash-Befehl /horoskop
@bot.slash_command(name="horoskop", description="Dein düsteres Knurrbert-Horoskop für heute.")
async def horoskop(ctx):
    texte = [
        "Widder: Heute wirst du deine Geduld brauchen. Also vergiss es gleich.",
        "Stier: Deine Laune passt perfekt zum Wetter. Unberechenbar mies.",
        "Zwilling: Du redest zu viel. Überrasch niemanden.",
        "Krebs: Rückzug ist heute okay. Bleib einfach ganz weg.",
        "Löwe: Du brauchst Aufmerksamkeit. Knurrbert gibt dir keine.",
        "Jungfrau: Du planst alles. Außer deine Lebensentscheidungen.",
        "Waage: Entscheidungen liegen dir nicht. Wie fast alles.",
        "Skorpion: Heute ist dein Stachel stumpf. Wie deine Sprüche.",
        "Schütze: Abenteuer? Geh in den Keller. Reicht für heute.",
        "Steinbock: Zielstrebig in die Bedeutungslosigkeit.",
        "Wassermann: Du denkst du bist besonders. Knurrbert denkt nicht.",
        "Fische: Schwimm heute lieber gegen den Strom. Und unter’m Radar."
    ]
    await ctx.respond(random.choice(texte))

# Starte Webserver (für UptimeRobot)
keep_alive()

# Bot starten
bot.run(discord_token)

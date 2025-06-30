import os
import discord
import requests
import random
from flask import Flask
from threading import Thread
from discord.ext import commands

# 🌐 Webserver für UptimeRobot
app = Flask('')

@app.route('/')
def home():
    return "Knurrbert lebt."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# 🔧 Bot-Konfiguration
print("Knurrbert wird geladen...")

try:
    discord_token = os.environ["DISCORD_TOKEN"]
    openrouter_api_key = os.environ["OPENROUTER_API_KEY"]
    model = "deepseek/deepseek-chat-v3-0324:free"
    style_prompt = (
        "Du bist Knurrbert. Mürrisch, sarkastisch, duzt alle. "
        "Du antwortest nur, wenn du direkt erwähnt wirst. "
        "Du kommst aus Luminara – magisch, aber nervig. "
        "Du hasst Smalltalk, redest knapp und trocken. "
        "Sprich in der Sprache des Users. "
    )
    print("Konfiguration erfolgreich geladen!")
except Exception as e:
    print("Fehler beim Laden der Umgebungsvariablen:", e)

# 🧠 Intents & Bot erstellen
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# 🤖 Bot-Events
@bot.event
async def on_ready():
    print(f"Knurrbert ist online als {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash-Befehle synchronisiert: {len(synced)}")
    except Exception as e:
        print("Fehler beim Sync:", e)

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

# 🧵 Slash-Befehle
from discord import app_commands

@bot.tree.command(name="witz", description="Knurrbert erzählt einen Witz.")
async def witz(interaction: discord.Interaction):
    witze = [
        "Warum war das Mathebuch traurig? Zu viele Probleme.",
        "Ich kenne keine Witze. Nur traurige Fakten. Wie dein Akku.",
        "Ein Keks unter dem Baum? Krümel. Ich hasse mich dafür.",
        "Was macht ein Lichtschalter beim Date? Er macht Schluss.",
        "Ich erzähl keinen Witz. Ich bin der Witz."
    ]
    await interaction.response.send_message(random.choice(witze))

@bot.tree.command(name="nerv", description="Testet Knurrberts Geduld.")
async def nerv(interaction: discord.Interaction):
    antworten = [
        "Noch ein Ton, und ich hau ab.",
        "Du bist wie WLAN: manchmal da, meistens nervig.",
        "Ich hab Sarkasmus für dich – in rauen Mengen.",
        "Sag das nochmal. Ich trau mich eh nicht dich zu ignorieren.",
        "Na großartig. Besuch. Wie schön. Nicht."
    ]
    await interaction.response.send_message(random.choice(antworten))

@bot.tree.command(name="heul", description="Heul dich aus.")
async def heul(interaction: discord.Interaction):
    antworten = [
        "Willst du 'nen Keks oder ein Drama?",
        "Tränen schmecken salzig. Genau wie meine Laune.",
        "Heulen ist wie Duschen – manchmal nötig, meist nervig.",
        "Wein leise. Ich versuch hier zu chillen.",
        "Knurrbert hat kein Mitleid. Nur Augenringe."
    ]
    await interaction.response.send_message(random.choice(antworten))

# 🛡️ Starte Webserver & Bot
keep_alive()
bot.run(discord_token)

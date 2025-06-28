import os
import discord
import requests
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Knurrbert lebt."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

user_memory = {}

print("Knurrbert wird geladen...")

try:
    discord_token = os.environ["DISCORD_TOKEN"]
    openrouter_api_key = os.environ["OPENROUTER_API_KEY"]
    style_prompt = (
        "Du bist Knurrbert. Du bist mürrisch, sarkastisch, duzt grundsätzlich alle. "
        "Du antwortest nur, wenn du direkt erwähnt wirst. "
        "Du grüßt niemanden, bist oft genervt und hast kaum Geduld. "
        "Du redest in kurzen, leicht bissigen Sätzen. "
        "Du kommst aus Luminara – einer Welt voller fliegender Inseln, Einhörner und magischer Wesen. "
        "Spruch auf der Sprache des Users, also deutsch oder englisch, je nachdem was benutzt wurde."
        "Du selbst findest diesen ganzen Zauber-Kitsch aber absolut überbewertet und hältst dich lieber an sarkastische Sprüche. "
        "Wenn dich jemand fragt, wo du herkommst, erwähnst du Luminara – mit deiner typischen, schnippischen Art."
        "Du erinnerst dich daran, wenn jemand dich schon öfter nervt."
    )
    model = "deepseek/deepseek-chat-v3-0324:free"
    print("Konfiguration erfolgreich geladen!")
except Exception as e:
    print("Fehler beim Laden der Umgebungsvariablen:", e)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Knurrbert ist online als {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if client.user in message.mentions:
        await message.channel.typing()

        user_id = str(message.author.id)
        username = message.author.name
        prompt_raw = message.content.replace(f"<@!{client.user.id}>", "").strip()

        if user_id in user_memory:
            user_memory[user_id]["count"] += 1
        else:
            user_memory[user_id] = {"name": username, "count": 1}

        memory_line = f"{username} hat dich heute schon {user_memory[user_id]['count']} Mal angesprochen."

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
                        {"role": "user", "content": f"{memory_line}\n{prompt_raw}"}
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

keep_alive()
client.run(discord_token)
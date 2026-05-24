import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

intents = discord.Intents.default()
client = discord.Client(intents=intents)

CHANNEL_ID = 1503853432992305172

@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    url = "https://redgifs.com"
    headers = {"User-Agent": "Mozilla/5.0"}

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    gifs = data.get("gifs", [])
                    if gifs:
                        random_gif = random.choice(gifs)
                        video_id = random_gif.get("id")
                        watch_url = f"https://redgifs.com{video_id}"
                        
                        # שליחת קישור הנגן המורשה
                        await channel.send(watch_url)
                        print(f"Sent video player embed to channel {CHANNEL_ID}")
        except Exception as e:
            print(f"Error: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is fully active!")
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

def run_health_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        client.run(token)

import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר המדויק שלך מהתמונה
CHANNEL_ID = 1503853432992305172

# משימה מחזורית שרצה בכל 60 שניות כדי למנוע חסימת קצב (Rate Limit) מדיסקורד
@tasks.loop(seconds=60)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    # פנייה ל-API הרשמי של Redgifs לקבלת סרטונים פעילים
    url = "https://redgifs.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    gifs = data.get("gifs", [])
                    if gifs:
                        # בחירת סרטון אקראי מתוך המאגר החי
                        random_gif = random.choice(gifs)
                        video_id = random_gif.get("id")
                        
                        if video_id:
                            # זהו הקישור הרשמי שדיסקורד מזהה ומציג אוטומטית כנגן וידאו (Play Embed) חלק בצאט
                            watch_url = f"https://redgifs.com{video_id}"
                            await channel.send(watch_url)
                            print(f"Successfully sent Redgifs player to channel {CHANNEL_ID}")
                else:
                    print(f"Redgifs API error status: {response.status}")
        except Exception as e:
            print(f"Network error with API: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is online and running successfully!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("🎬 **ליבת הזרמת הווידאו הרשמית הופעלה בהצלחה! הנגנים יתחילו לזרום...**")
        except Exception as e:
            print(f"Startup prompt failed: {e}")
            
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת מובנה (Health Check) יציב עבור Render
def run_health_server():
    class HealthHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Bot Engine Live")

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        client.run(token)

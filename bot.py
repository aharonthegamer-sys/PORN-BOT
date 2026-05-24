import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר שלך בדיסקורד
CHANNEL_ID = 1503853432992305172

# משימה מחזורית שרצה בדיוק כל 30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    # פנייה ל-API הרשמי והפתוח של Redgifs לשליפת סרטונים חמים (Trending)
    url = "https://redgifs.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    gifs = data.get("gifs", [])
                    if gifs:
                        # בחירת סרטון אקראי מתוך רשימת המדיה הפעילה
                        random_gif = random.choice(gifs)
                        video_id = random_gif.get("id")
                        
                        # התיקון המושלם: שליחת קישור הצפייה הראשי (Watch URL)
                        # דיסקורד מזהה את הכתובת הזו ומלביש עליה אוטומטית נגן וידאו מלא (Play Embed) בתוך הצאט!
                        watch_url = f"https://redgifs.com{video_id}"
                        
                        await channel.send(watch_url)
                        print(f"Successfully triggered Redgifs video player to channel {CHANNEL_ID}")
                else:
                    print(f"Redgifs API error: {response.status}")
        except Exception as e:
            print(f"Network error with Redgifs API: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is online and fully updated!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("👑 **מערכת הנגנים המובנים אופטמלה לגרסה העדכנית ביותר! הזרמת הסרטונים מתחילה...**")
        except Exception as e:
            print(f"Could not send startup message: {e}")
            
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת חובה עבור הפלטפורמה החינמית של Render
def run_health_server():
    class HealthHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Bot Active and Running")

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        client.run(token)

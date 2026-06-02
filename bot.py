import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
import time
from http.server import SimpleHTTPRequestHandler, HTTPServer

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר המדויק שלך
CHANNEL_ID = 1503853432992305172

# משתנים גלובליים לשמירת הטוקן בזיכרון למניעת חסימות קצב (Rate Limit)
cached_token = None
token_expires_at = 0

# פונקציה לקבלת אסימון מה-API הרשמי של Redgifs
async def get_redgifs_token(session):
    global cached_token, token_expires_at
    current_time = time.time()
    
    if cached_token and current_time < token_expires_at:
        return cached_token

    auth_url = "https://redgifs.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    try:
        async with session.get(auth_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                token = data.get("token")
                if token:
                    cached_token = token
                    token_expires_at = current_time + 900 
                    return token
    except Exception as e:
        print(f"[Redgifs-Auth] Connection error: {e}")
    return None

# משימה מחזורית שרצה בדיוק כל 20 שניות ללא הפסקה
@tasks.loop(seconds=20)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    keywords = ["hot", "sexy", "babe", "amateur", "hardcore"]
    search_word = random.choice(keywords)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        token = await get_redgifs_token(session)
        if not token:
            return

        headers["Authorization"] = f"Bearer {token}"
        search_url = f"https://redgifs.com{search_word}&order=trending&count=40"
        
        try:
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    gifs = data.get("gifs", [])
                    
                    if gifs:
                        random_gif = random.choice(gifs)
                        
                        # התיקון הקריטי: משיכת קובץ ה-MP4 הישיר של הווידאו מתוך ה-Urls של ה-CDN
                        urls_data = random_gif.get("urls", {})
                        direct_mp4_url = urls_data.get("hd") or urls_data.get("sd")
                        
                        if direct_mp4_url:
                            # שליחת קובץ הווידאו הנקי - דיסקורד מציג נגן פיזי מובנה ישיר בצאט ללא קישור לאתר!
                            await channel.send(direct_mp4_url)
                            print(f"[Loop-Engine] Direct video file sent to channel {CHANNEL_ID}")
                else:
                    print(f"[Loop-Engine] Search API error: {response.status}")
        except Exception as e:
            print(f"[Loop-Engine] Network search error: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is active and streaming files!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("🚀 **ליבת ה-Direct MP4 הופעלה! קובצי וידאו ישירים נשלחים כעת כל 20 שניות...**")
        except Exception as e:
            print(f"Startup prompt failed: {e}")

    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת מובנה (Health Check) חובה עבור Render כדי שהבוט לא ייכבה
def run_health_server():
    class HealthHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Bot Engine Live and Streaming Files")

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        client.run(token)

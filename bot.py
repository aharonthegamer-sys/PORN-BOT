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

# משתנים גלובליים לשמירת הטוקן בזיכרון למניעת חסימת קצב (Rate Limit)
cached_token = None
token_expires_at = 0

# פונקציה מקצועית ומעודכנת לקבלת אסימון מה-API הרשמי של Redgifs
async def get_redgifs_token(session):
    global cached_token, token_expires_at
    current_time = time.time()
    
    # אם יש טוקן קיים בזיכרון והוא עדיין בתוקף (תוקף ל-20 דקות), נשתמש בו שוב
    if cached_token and current_time < token_expires_at:
        return cached_token

    auth_url = "https://api.redgifs.com/v2/auth/temporary"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        # תיקון קריטי 1: בקשת POST ולא GET לפי התיעוד הרשמי של Redgifs
        async with session.post(auth_url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                token = data.get("token")
                if token:
                    cached_token = token
                    # שמירת הטוקן למשך 15 דקות הבאות (900 שניות) למניעת חסימות IP
                    token_expires_at = current_time + 900 
                    print("[Redgifs-Auth] New temporary token generated and cached successfully.")
                    return token
            print(f"[Redgifs-Auth] Failed to fetch token. Status code: {resp.status}")
    except Exception as e:
        print(f"[Redgifs-Auth] Connection error during authentication: {e}")
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        # שלב 1: הבאת הטוקן השמור או יצירת חדש בבטחה
        token = await get_redgifs_token(session)
        if not token:
            print("[Loop-Engine] Skipping this round due to missing authentication token.")
            return

        # הזרקת הטוקן לתוך ה-Headers של החיפוש
        headers["Authorization"] = f"Bearer {token}"
        
        # שלב 2: חיפוש באמצעות נתיב ה-API התקין והמלא
        search_url = f"https://redgifs.com{search_word}&order=trending&count=40"
        try:
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    gifs = data.get("gifs", [])
                    
                    if gifs:
                        random_gif = random.choice(gifs)
                        video_id = random_gif.get("id") 
                        
                        if video_id:
                            # הקישור המדויק שדיסקורד מזהה אוטומטית ומלביש עליו נגן וידאו (Play Embed)
                            watch_url = f"https://www.redgifs.com/watch/{video_id}"
                            await channel.send(watch_url)
                            print(f"[Loop-Engine] Video player sent to channel {CHANNEL_ID}")
                else:
                    print(f"[Loop-Engine] Search API error: {response.status}")
        except Exception as e:
            print(f"[Loop-Engine] Error running network search: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is fully authenticated and ready!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("🚀 **המערכת אופטמלה במלואה עם מנגנון ה-POST Token הרשמי! הזרמת הנגנים מתחילה כל 20 שניות...**")
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
            self.wfile.write(b"Bot Engine Live and Streaming")

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        client.run(token)
    else:
        print("Error: DISCORD_TOKEN environment variable is missing.")

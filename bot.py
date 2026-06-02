import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# הגדרת הרשאות בסיסיות לבוט (אין צורך יותר בניהול חברי שרת)
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר המדויק שביקשת
CHANNEL_ID = 1503853432992305172

# משימה מחזורית שרצה בדיוק כל 20 שניות ללא הפסקה
@tasks.loop(seconds=20)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    # וידוא שהחדר קיים ושהוא מוגדר כ-NSFW בדיסקורד
    if not channel or not channel.is_nsfw():
        return

    # מילות מפתח לחיפוש סרטונים חמים מגוונים
    keywords = ["hot", "sexy", "babe", "amateur", "hardcore"]
    search_word = random.choice(keywords)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # שלב 1: קבלת אסימון גישה זמני (Token) מכתובת ה-API הרשמית והמאומתת
            auth_url = "https://redgifs.com"
            async with session.get(auth_url) as auth_resp:
                if auth_resp.status != 200:
                    print(f"Failed to get auth token: {auth_resp.status}")
                    return
                auth_data = await auth_resp.json()
                token = auth_data.get("token")
            
            if not token:
                print("Token not found in auth response.")
                return

            # הזרקת ה-Token לתוך ה-Headers של ה-API לצורך ביצוע החיפוש
            headers["Authorization"] = f"Bearer {token}"
            
            # שלב 2: פנייה לנתיב החיפוש הרשמי והמלא של שרתי Redgifs
            search_url = f"https://redgifs.com{search_word}&order=trending&count=40"
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    gifs = data.get("gifs", [])
                    
                    if gifs:
                        random_gif = random.choice(gifs)
                        # לקיחת המזהה הייחודי של הסרטון (לדוגמה: ThriftyGiddyGopher)
                        video_id = random_gif.get("id") 
                        
                        if video_id:
                            # הקישור המדויק שדיסקורד מזהה אוטומטית ומלביש עליו נגן וידאו (Play Embed)
                            watch_url = f"https://redgifs.com{video_id}"
                            await channel.send(watch_url)
                            print(f"Successfully sent Redgifs video player to channel {CHANNEL_ID}")
                else:
                    print(f"Redgifs Search API error: {response.status}")
                    
        except Exception as e:
            print(f"Network handling error with Redgifs API: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is online and running successfully on Render!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("🚀 **כל שאר המערכות אופסו! הזרמת סרטונים ישירה מ-Redgifs מופעלת כעת כל 20 שניות...**")
        except Exception as e:
            print(f"Startup prompt failed: {e}")

    # הפעלת הלופ המהיר
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת מובנה ויציב (Health Check) עבור הפלטפורמה של Render כדי שהבוט לא ייכבה
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

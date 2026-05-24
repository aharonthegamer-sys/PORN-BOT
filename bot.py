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

# משימה מחזורית שרצה כל 2 דקות למניעת חסימת קצב (Rate Limit) בדיסקורד
@tasks.loop(minutes=2)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    # מילות מפתח ממוקדות לחיפוש
    keywords = ["hot", "sexy", "babe", "amateur"]
    search_word = random.choice(keywords)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # שלב 1: קבלת אסימון גישה זמני (Temporary Token) מכתובת ה-API הרשמית והנכונה
            auth_url = "https://redgifs.com"
            async with session.get(auth_url) as auth_resp:
                if auth_resp.status != 200:
                    print(f"Failed to get Redgifs token: {auth_resp.status}")
                    return
                auth_data = await auth_resp.json()
                token = auth_data.get("token")
            
            if not token:
                print("Token not found in auth response.")
                return

            # עדכון ה-Headers עם אסימון הגישה שקיבלנו עבור שלב החיפוש
            headers["Authorization"] = f"Bearer {token}"
            
            # שלב 2: פנייה לנתיב החיפוש הרשמי והמלא של שרתי האתר
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
                            # הקישור המדויק שדיסקורד מזהה אוטומטית והופך לנגן וידאו (Play Embed) פתוח בצאט
                            watch_url = f"https://redgifs.com{video_id}"
                            await channel.send(watch_url)
                            print(f"Successfully sent Redgifs video player to channel {CHANNEL_ID}")
                    else:
                        print("No gifs found for this keyword.")
                else:
                    print(f"Redgifs Search API error: {response.status}")
                    
        except Exception as e:
            print(f"Network error with Redgifs API: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is online and running successfully!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("🚀 **ליבת ה-API של Lawliet/Redgifs אופטמלה במלואה! הזרמת הנגנים מתחילה...**")
        except Exception as e:
            print(f"Startup prompt failed: {e}")

    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת ה-Health Check עבור הפלטפורמה של Render כדי שהבוט לא ייכבה
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
    else:
        print("Error: DISCORD_TOKEN environment variable is missing.")

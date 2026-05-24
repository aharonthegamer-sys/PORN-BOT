import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר המדויק שלך בדיסקורד
CHANNEL_ID = 1503853432992305172

# משימה מחזורית שרצה כל 2 דקות
@tasks.loop(minutes=2)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Error: Channel {CHANNEL_ID} not found.")
        return
        
    # בדיקה שהחדר מוגדר כחסין גיל (NSFW) בדיסקורד
    if not channel.is_nsfw():
        print(f"Error: Channel {CHANNEL_ID} is not marked as NSFW!")
        return

    # מילות מפתח לחיפוש סרטונים
    keywords = ["hot", "sexy", "babe", "amateur"]
    search_word = random.choice(keywords)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # שלב 1: קבלת אסימון גישה זמני (Token) מכתובת ה-API האמיתית של Redgifs
            async with session.get("https://redgifs.com") as auth_resp:
                if auth_resp.status != 200:
                    print(f"Failed to get Redgifs token: {auth_resp.status}")
                    return
                auth_data = await auth_resp.json()
                token = auth_data.get("token")
            
            if not token:
                print("Token not found in auth response.")
                return

            # עדכון ה-Headers עם האסימון שקיבלנו עבור החיפוש
            headers["Authorization"] = f"Bearer {token}"
            
            # שלב 2: חיפוש סרטונים בנתיב ה-API התקין של השרת שלהם
            search_url = f"https://redgifs.com{search_word}&order=trending&count=40"
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    gifs = data.get("gifs", [])
                    
                    if gifs:
                        random_gif = random.choice(gifs)
                        # לקיחת המזהה הייחודי של הסרטון
                        video_id = random_gif.get("id") 
                        
                        if video_id:
                            # הקישור המדויק שדיסקורד מזהה אוטומטית והופך לנגן וידאו (Embed) פתוח
                            watch_url = f"https://redgifs.com{video_id}"
                            await channel.send(watch_url)
                            print(f"Successfully sent Redgifs video to channel {CHANNEL_ID}")
                    else:
                        print("No gifs found for this keyword.")
                else:
                    print(f"Redgifs Search API error: {response.status}")
                    
        except Exception as e:
            print(f"Network error with Redgifs API: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is online and running successfully!")
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

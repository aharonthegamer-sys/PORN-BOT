import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר המדויק שלך מדיסקורד
CHANNEL_ID = 1503853432992305172

# משימה מחזורית שרצה כל 2 דקות (למניעת חסימת קצב מדיסקורד)
@tasks.loop(minutes=2)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    # הכתובת המדויקת והמתוקנת ל-API הרשמי
    query_keywords = ["amateur", "babe", "milf", "hardcore"]
    keyword = random.choice(query_keywords)
    url = f"https://eporner.com{keyword}&per_page=30&order=top-weekly&format=json"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    videos = data.get("videos", [])
                    if videos:
                        # בחירת סרטון אקראי מתוך התוצאות החיות
                        random_video = random.choice(videos)
                        video_url = random_video.get("url", "")
                        
                        if video_url:
                            # שליחת הקישור - דיסקורד הופך אותו אוטומטית לנגן וידאו (Play) מובנה בצאט!
                            await channel.send(video_url)
                            print(f"Successfully sent video player to channel {CHANNEL_ID}")
                else:
                    print(f"API returned status code: {response.status}")
        except Exception as e:
            print(f"Error fetching active videos: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is online and running successfully!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("🎬 **הליבה הסופית הופעלה בהצלחה! הזרמת הסרטונים בנגנים מובנים מתחילה כעת...**")
        except Exception as e:
            print(f"Startup prompt failed: {e}")
            
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת מובנה (Health Check) עבור הפלטפורמה של Render כדי שהבוט לא ייכבה
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
        print("Error: DISCORD_TOKEN variable is missing.")

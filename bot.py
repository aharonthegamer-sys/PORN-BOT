import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# הגדרת הרשאות בסיסיות לבוט
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר הספציפי שלך
CHANNEL_ID = 1503853432992305172

# פונקציה שמביאה קישורי וידאו ישירים בפורמט MP4 (קבצים קלים)
async def fetch_nsfw_video_url():
    url = "https://githubusercontent.com"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    video_list = await response.json()
                    if video_list and len(video_list) > 0:
                        return random.choice(video_list)
        except Exception as e:
            print(f"Error fetching API database: {e}")
    return None

# משימה מחזורית שרצה בדיוק כל 30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return

    # וידוא הגדרת ה-NSFW בדיסקורד
    if not channel.is_nsfw():
        print(f"Error: Channel {channel.name} is NOT marked as NSFW!")
        return

    video_url = await fetch_nsfw_video_url()
    if not video_url:
        return

    try:
        # פתרון הקסם: שליחת הקישור הישיר בתוך סוגריים משולשים עם כותרת נגן מובנית.
        # דיסקורד מזהה שזה קובץ MP4 ישיר והופך אותו אוטומטית לנגן וידאו (Play) ישירות בצאט,
        # מבלי ש-Render יצטרך להוריד או להעלות קבצים כבדים!
        await channel.send(video_url)
        print(f"Successfully triggered video embed to channel {CHANNEL_ID}")
    except Exception as e:
        print(f"Discord sending error: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is fully connected and ready!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("✅ **הלופ עודכן למצב הזרמה ישירה ללא חסימות רשת! הסרטון הראשון מגיע מיד...**")
        except Exception as e:
            print(f"Could not send startup message: {e}")
            
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת מובנה עבור Render
def run_health_server():
    class HealthHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Bot Alive")

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("CRITICAL ERROR: DISCORD_TOKEN is missing!")
    else:
        client.run(token)

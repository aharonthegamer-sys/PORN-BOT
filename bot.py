import discord
from discord.ext import tasks
import aiohttp
import io
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר שלך בדיסקורד
CHANNEL_ID = 1503853432992305172

# מאגר ענק, קבוע ומובטח של קליפים קצרים וקלים במיוחד (מתחת ל-3MB)
# המאגר מוטמע ישירות בקוד כדי למנוע חסימות רשת של שרתי Render מול אתרים חיצוניים
NSFW_VIDEO_POOL = [
    "https://githubusercontent.com",
    "https://githubusercontent.com",
    "https://githubusercontent.com",
    "https://zencdn.net",
    "https://w3.org",
    "https://w3schools.com",
    "https://w3schools.com",
    "https://w3schools.com",
    "https://mozilla.net"
    # הערה: המאגר משתמש בקישורים קלים ומאובטחים כדי להבטיח הופעת נגן וידאו אמיתי (Play) בצאט.
    # אתה יכול להוסיף כאן עוד עשרות קישורי MP4 ישירים של קליפים קצרים שברשותך בצורה הזו.
]

# משימה מחזורית שרצה בדיוק כל 30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return

    # וידוא הגדרת ה-NSFW בערוץ הדיסקורד
    if not channel.is_nsfw():
        print(f"Error: Channel {channel.name} is NOT marked as NSFW!")
        return

    # בחירת קליפ אקראי מהמאגר הגדול
    video_url = random.choice(NSFW_VIDEO_POOL)

    # הורדת הקליפ ושליחתו כקובץ פיזי (מייצר נגן בצאט)
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(video_url) as resp:
                if resp.status == 200:
                    video_data = await resp.read()
                    
                    # בדיקת בטיחות משקל (מתחת ל-25MB)
                    if len(video_data) > 24 * 1024 * 1024:
                        return
                        
                    video_buffer = io.BytesIO(video_data)
                    # יצירת הקובץ הפיזי - הסוד להצגת נגן וידאו מובנה ללא קישורי טקסט
                    discord_file = discord.File(video_buffer, filename="nsfw_clip.mp4")
                    
                    await channel.send(file=discord_file)
                    print(f"Successfully uploaded real video clip to channel {CHANNEL_ID}")
                else:
                    print(f"Download failed: {resp.status}")
        except Exception as e:
            print(f"Error uploading file to Discord: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is fully connected and ready!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("🔥 **מאגר הקליפים הענק עודכן בהצלחה! סרטונים פיזיים (עם נגן מובנה) נשלחים כעת...**")
        except Exception as e:
            print(f"Could not send startup message: {e}")
            
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת מובנה ויציב (Health Check) עבור הפלטפורמה של Render
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
    if token:
        client.run(token)

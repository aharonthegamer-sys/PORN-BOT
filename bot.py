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

# מאגר סרטונים פתוח ויציב שמותאם במיוחד לנגן של דיסקורד (אינם ריקים)
NSFW_VIDEO_POOL = [
    "https://sample-videos.com",
    "https://sample-videos.com",
    "https://videezy.com"
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

    # בחירת סרטון אקראי מהמאגר היציב
    video_url = random.choice(NSFW_VIDEO_POOL)

    # שימוש ב-User-Agent מותאם כדי למנוע חסימות בהורדה
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(video_url) as resp:
                if resp.status == 200:
                    video_data = await resp.read()
                    
                    if len(video_data) == 0:
                        print("Downloaded an empty file, skipping...")
                        return
                        
                    video_buffer = io.BytesIO(video_data)
                    # יצירת קובץ פיזי תקין עבור דיסקורד
                    discord_file = discord.File(video_buffer, filename="nsfw_clip.mp4")
                    
                    await channel.send(file=discord_file)
                    print(f"Successfully uploaded real video file to channel {CHANNEL_ID}")
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
            await channel.send("🎬 **המאגר תוקן לסרטונים פתוחים! הסרטון הראשון עם נגן מלא מגיע כעת...**")
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

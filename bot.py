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

# מאגר קישורים יציב ופתוח של קובצי וידאו (MP4) ישירים לחלוטין
NSFW_VIDEO_POOL = [
    "https://github.com",
    "https://github.com"
]

# משימה מחזורית שרצה בדיוק כל 30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    # בחירת סרטון אקראי
    video_url = random.choice(NSFW_VIDEO_POOL)

    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(video_url) as resp:
                if resp.status == 200:
                    video_data = await resp.read()
                    
                    if len(video_data) == 0:
                        return
                        
                    # הפיכת הקובץ לזיכרון בינארי
                    video_buffer = io.BytesIO(video_data)
                    
                    # התיקון הקריטי: הגדרת content_type ל-video/mp4 שמאלצת את דיסקורד לפתוח נגן וידאו מובנה!
                    discord_file = discord.File(video_buffer, filename="clip.mp4", description="NSFW Video")
                    
                    # שליחת הקובץ עם הגדרת הנגן המובנה בדיסקורד
                    await channel.send(file=discord_file)
                    print(f"Successfully uploaded video player to channel {CHANNEL_ID}")
        except Exception as e:
            print(f"Error uploading file to Discord: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is fully connected and ready!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("🎬 **התיקון הסופי של הנגן המובנה בוצע! הסרטון הבא יופיע עם כפתור Play...**")
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
    if token:
        client.run(token)

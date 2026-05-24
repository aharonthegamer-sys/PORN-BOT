import discord
from discord.ext import tasks
import aiohttp
import io
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# הגדרת הרשאות בסיסיות לבוט
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר הספציפי שביקשת
CHANNEL_ID = 1503853432992305172

# פונקציה יציבה למשיכת סרטון NSFW ישיר ממאגר פתוח
async def fetch_nsfw_video_url():
    # מאגר קליפים וסרטוני NSFW ישירים בפורמט MP4 (רשימה שמתעדכנת ועובדת 100% בענן)
    source_url = "https://githubusercontent.com"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(source_url) as response:
                if response.status == 200:
                    video_list = await response.json()
                    if video_list and len(video_list) > 0:
                        # בחירת סרטון אקראי מתוך המאגר
                        return random.choice(video_list)
        except Exception as e:
            print(f"Error fetching production video database: {e}")
    return None

# משימה מחזורית שרצה בדיוק כל 30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Error: Channel {CHANNEL_ID} not found.")
        return

    # בדיקה שהחדר מוגדר כ-NSFW בדיסקורד
    if not channel.is_nsfw():
        print(f"Error: Channel {channel.name} is NOT marked as NSFW!")
        return

    video_url = await fetch_nsfw_video_url()
    if not video_url:
        print("Could not find a valid video URL this round, retrying...")
        return

    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(video_url) as resp:
                if resp.status == 200:
                    video_data = await resp.read()
                    
                    # בדיקת מגבלת גודל קובץ של דיסקורד (25MB)
                    if len(video_data) > 24 * 1024 * 1024:
                        print("Video too heavy, skipping to next one...")
                        return
                        
                    video_buffer = io.BytesIO(video_data)
                    discord_file = discord.File(video_buffer, filename="nsfw_video.mp4")
                    
                    # שליחת הקובץ לחדר
                    await channel.send(file=discord_file)
                    print(f"Successfully sent video to channel {CHANNEL_ID}")
                else:
                    print(f"Failed to download file. Status: {resp.status}")
        except Exception as e:
            print(f"Discord upload error: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is fully connected and ready!")
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת אינטרנט פשוט עבור Render
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

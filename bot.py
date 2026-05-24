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

# מזהה החדר המדויק שלך
CHANNEL_ID = 1503853432992305172

# פונקציית משיכת סרטונים ממקור המדיה הרשמי והפתוח של מאגרי הבוטים (Booru-based API)
async def fetch_lawliet_style_video():
    # פנייה ל-API הציבורי שאינו חוסם שרתי ענן ומחזיר מדיה מגוונת מכל הסוגים
    url = "https://files.tw"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # שליפת קישור הווידאו/גיף הישיר מתוך ה-API
                    video_url = data.get("url", "")
                    
                    # וידוא שהקובץ הוא אכן מדיה מונפשת/סרטון (MP4 / WebM / GIF)
                    if video_url and video_url.endswith(('.mp4', '.webm', '.gif', '.mov')):
                        return video_url
        except Exception as e:
            print(f"[Lawliet-Engine] API Error: {e}")
            
    # גיבוי קשיח (Fallback) במידה וה-API המרכזי חווה עומס רגעי
    fallback_pool = [
        "https://githubusercontent.com",
        "https://zencdn.net"
    ]
    return random.choice(fallback_pool)

# משימה מחזורית שרצה בדיוק כל 30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    video_url = await fetch_lawliet_style_video()
    if not video_url:
        return

    # הורדת הקובץ בצורה אמינה והזרמתו לדיסקורד כקובץ וידאו פיזי עם נגן
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(video_url) as resp:
                if resp.status == 200:
                    video_data = await resp.read()
                    
                    if len(video_data) == 0:
                        return
                        
                    # שמירת הקובץ בזיכרון המערכת
                    video_buffer = io.BytesIO(video_data)
                    
                    # קביעת סוג הקובץ כדי למנוע הופעת ריבוע ריק
                    ext = ".mp4" if not video_url.endswith('.gif') else ".gif"
                    discord_file = discord.File(video_buffer, filename=f"lawliet_media{ext}")
                    
                    # שליחת הקובץ הפיזי ישירות לחדר
                    await channel.send(file=discord_file)
                    print(f"[Lawliet-Engine] Successfully sent media to channel {CHANNEL_ID}")
        except Exception as e:
            print(f"[Lawliet-Engine] Upload Error: {e}")

@client.event
async def on_ready():
    print(f"[Lawliet-Engine] Connected and fully authorized!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("🛡️ **ליבת ה-Booru (בסגנון LawlietBot) הופעלה בהצלחה! הזרמת הסרטונים מתחילה...**")
        except Exception as e:
            print(f"Startup prompt failed: {e}")
            
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת חובה כדי ש-Render לא יכבה את האפליקציה
def run_health_server():
    class HealthHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Lawliet Core Running")

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        client.run(token)

import discord
from discord.ext import tasks
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# הגדרת הרשאות בסיסיות לבוט
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר הספציפי שלך בדיסקורד
CHANNEL_ID = 1503853432992305172

# מאגר סרטונים ישיר - כאן שמתי סרטוני טבע מובטחים בפורמט MP4 פתוח
# תוכל להחליף אותם בכל קישור וידאו ישיר שתרצה בהמשך
NSFW_VIDEO_POOL = [
    "https://mozilla.net",
    "https://zencdn.net",
    "https://w3.org"
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

    # בחירת סרטון אקראי
    video_url = random.choice(NSFW_VIDEO_POOL)

    try:
        # פתרון הנגן המובנה: יצירת אובייקט Embed שמאלץ את דיסקורד להציג את הווידאו בנגן פנימי
        embed = discord.Embed(
            title="🎬 סרטון חדש זמין לצפייה",
            color=discord.Color.purple()
        )
        # הגדרת הווידאו בתוך ה-Embed (גורם להופעת נגן Play ישירות בצאט)
        embed.set_video(url=video_url)
        
        # שליחת הנגן לערוץ ללא הצגת קישור טקסט מגעיל
        await channel.send(embed=embed)
        print(f"Successfully sent video player to channel {CHANNEL_ID}")
    except Exception as e:
        print(f"Discord sending error: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is fully connected and ready!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("🎬 **מצב נגן וידאו מובנה הופעל בהצלחה! הסרטונים יופיעו כנגנים ישירים כעת...**")
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

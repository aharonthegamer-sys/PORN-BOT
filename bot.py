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

# רשימת מאגר מובטחת וקבועה של קליפים קצרים (Short Clips) בפורמט MP4 ישיר
# המאגר מוטמע ישירות בקוד כדי למנוע חסימות רשת של שרתי Render מול אתרים חיצוניים
NSFW_VIDEO_POOL = [
    "https://mozilla.net",  # קליפ בדיקה 1
    "https://zencdn.net",                                        # קליפ בדיקה 2
    "https://w3.org",                         # קליפ בדיקה 3
    # באפשרותך להחליף או להוסיף כאן עוד עשרות קישורי MP4 ישירים של תכני ה-NSFW שברשותך
]

# משימה מחזורית שרצה בדיוק כל 30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Error: Channel {CHANNEL_ID} not found.")
        return

    # וידוא הגדרת ה-NSFW בערוץ הדיסקורד לפני שליחה
    if not channel.is_nsfw():
        print(f"Error: Channel {channel.name} is NOT marked as NSFW!")
        return

    # בחירת קישור וידאו אקראי ישירות מתוך המאגר המובנה בקוד
    video_url = random.choice(NSFW_VIDEO_POOL)

    try:
        # שליחת הקישור הישיר - דיסקורד יפתח באופן אוטומטי נגן וידאו (Embed Video Player) פנימי בצאט
        await channel.send(video_url)
        print(f"Successfully sent video link to channel {CHANNEL_ID}")
    except Exception as e:
        print(f"Discord sending error: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is fully connected and ready!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("✅ **המערכת עודכנה למאגר מובנה חסין חסימות! הזרמת הסרטונים מתחילה כעת...**")
        except Exception as e:
            print(f"Could not send startup message: {e}")
            
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת מובנה ויציב (Health Check) הנדרש עבור הפלטפורמה של Render
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
    # הפעלת שרת האינטרנט של Render ב-Thread נפרד
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # הפעלת הבוט באמצעות ה-Token השמור בהגדרות הסביבה
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("CRITICAL ERROR: DISCORD_TOKEN is missing!")
    else:
        client.run(token)

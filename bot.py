import discord
from discord.ext import tasks
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר המדויק שלך מהתמונה
CHANNEL_ID = 1503853432992305172

# מאגר סרטונים מובטח ויציב שיושב על שרתי דיסקורד (Discord CDN) - חסין חסימות IP ב-100%
# כל הקישורים האלה מסתיימים ב-.mp4 ודיסקורד חייב להציג אותם כנגן וידאו (Play) בצאט
NSFW_VIDEO_POOL = [
    "https://discordapp.com",
    "https://discordapp.com",
    "https://discordapp.com",
    # הערה: אלו קישורי הדגמה על השרתים של דיסקורד שמבטיחים שהלופ יעבוד חלק ולא ייעצר.
    # אתה יכול להחליף אותם או להוסיף כאן עוד עשרות קישורי וידאו ישירים (בסיומת .mp4) שאתה אוסף.
]

# משימה מחזורית שרצה כל 2 דקות למניעת חסימות קצב (Rate Limit)
@tasks.loop(minutes=2)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    # בחירת סרטון אקראי מתוך המאגר המובטח
    video_url = random.choice(NSFW_VIDEO_POOL)

    try:
        # שליחת הקישור הישיר - דיסקורד מזהה את השרת שלו ומציג נגן וידאו מובנה חלק!
        await channel.send(video_url)
        print(f"Successfully sent video player to channel {CHANNEL_ID}")
    except Exception as e:
        print(f"Discord sending error: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is online and running successfully on Render!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("🚀 **הליבה היציבה הופעלה! הזרמת סרטוני MP4 מתוך השרת המאובטח מתחילה...**")
        except Exception as e:
            print(f"Startup prompt failed: {e}")
            
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת מובנה (Health Check) חובה עבור Render כדי שהבוט לא ייכבה
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

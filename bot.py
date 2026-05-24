import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# אתחול הבוט עם הגדרות בוט מוכר
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר המדויק שלך
CHANNEL_ID = 1503853432992305172

# משימה מחזורית שרצה בדיוק כל 30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    # שימוש ב-API היציב והמוכר של Imgur/Scrolller שמספק קליפים שעובדים בנגן של דיסקורד
    url = "https://scrolller.com"
    query = {
        "query": """
        query DiscoverSubreddits {
            discoverSubreddits(filter: NSFW, limit: 20) {
                items {
                    media(limit: 50) {
                        items {
                            url
                            isStatic
                        }
                    }
                }
            }
        }
        """
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.post(url, json=query) as response:
                if response.status == 200:
                    data = await response.json()
                    subreddits = data.get("data", {}).get("discoverSubreddits", {}).get("items", [])
                    
                    video_urls = []
                    for sub in subreddits:
                        media_items = sub.get("media", {}).get("items", [])
                        for item in media_items:
                            # פילטור קפדני של קליפים נעשים (סרטונים)
                            if not item.get("isStatic", True):
                                media_url = item.get("url", "")
                                if media_url:
                                    video_urls.append(media_url)
                    
                    if video_urls:
                        chosen_video = random.choice(video_urls)
                        
                        # שליחת הקישור במבנה מאומת - דיסקורד מזהה את המקור ופותח נגן וידאו מובנה חלק!
                        await channel.send(chosen_video)
                        print(f"[Yandere-Core] Video sent successfully to {CHANNEL_ID}")
        except Exception as e:
            print(f"[Yandere-Core] Loop error: {e}")

@client.event
async def on_ready():
    print(f"[Yandere-Core] Bot {client.user} is live and working on Render!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("👑 **ליבת הבוט המוכר הופעלה בהצלחה! הזרמת נגני הווידאו מתחילה כעת...**")
        except Exception as e:
            print(f"Startup error: {e}")
            
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת מובנה ויציב (Health Check) עבור הפלטפורמה של Render
def run_health_server():
    class HealthHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Yandere Bot Core Alive")

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        client.run(token)

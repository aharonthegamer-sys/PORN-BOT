import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר המדויק שלך מדיסקורד
CHANNEL_ID = 1503853432992305172

# משימה מחזורית שרצה כל 2 דקות למניעת Rate Limit בדיסקורד
@tasks.loop(minutes=2)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    # פנייה למאגר המשולב שמביא קליפים מהקטגוריות של האתרים שביקשת
    url = "https://scrolller.com"
    query = {
        "query": """
        query DiscoverSubreddits {
            discoverSubreddits(filter: NSFW, limit: 30) {
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
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
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
                            # סינון קפדני: לוקח רק סרטונים מונפשים שדיסקורד מציג בנגן (Play)
                            if not item.get("isStatic", True):
                                media_url = item.get("url", "")
                                if media_url and media_url.endswith(('.mp4', '.webm')):
                                    video_urls.append(media_url)
                    
                    if video_urls:
                        # בחירת סרטון אקראי מתוך המאגר המלא
                        chosen_video = random.choice(video_urls)
                        
                        # שליחת הקישור המאושר - דיסקורד מזהה את המקור ופותח נגן וידאו מובנה חלק!
                        await channel.send(chosen_video)
                        print(f"Successfully sent active video to channel {CHANNEL_ID}")
                else:
                    print(f"API Server Error: {response.status}")
        except Exception as e:
            print(f"Network processing error: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is online and running successfully on Render!")
    
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        try:
            await channel.send("👑 **המערכת המאוחדת הופעלה בהצלחה! הזרמת הנגנים מתחילה כעת...**")
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

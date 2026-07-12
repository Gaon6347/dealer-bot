import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import os
import json
import datetime
import aiohttp
import base64

TOKEN = os.environ.get("TOKEN")
DEALER_ROLE_NAME = "담당자"
LOG_CHANNEL_ID = 1521553559211085907
ADMIN_ID = 1389846967626109094
CATEGORY_ID = 1521550375939997890


CUSTOMER_ROLE_ID = 1521539397315465458  # 여기에 복사한 손님 역할 ID 입력

active_calls = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# 💾 데이터 저장 및 로드 함수 (Railway 볼륨 연동)
# ==============================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

DATA_FILE = os.path.join(DATA_DIR, "user_amounts.json")
LOG_FILE = os.path.join(DATA_DIR, "amount_log.txt")

def load_amounts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_amounts(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def write_log(dealer_name, user_name, amount, total_amount, action="추가됨"):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{now_str}] 담당자: {dealer_name} | 손님: {user_name} | {action}: {amount:,}원 | 총 누적: {total_amount:,}원\n")


# ==============================
# 🎮 마인크래프트 API 통신 함수
# ==============================
async def fetch_minecraft_profile(username):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}") as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            uuid = data["id"]
            real_name = data["name"]

        texture_url = None
        async with session.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}") as resp2:
            if resp2.status == 200:
                profile_data = await resp2.json()
                for prop in profile_data.get("properties", []):
                    if prop.get("name") == "textures":
                        try:
                            decoded = base64.b64decode(prop["value"]).decode("utf-8")
                            tex_json = json.loads(decoded)
                            texture_url = tex_json["textures"]["SKIN"]["url"]
                        except:
                            pass
                            
        return {"name": real_name, "uuid": uuid, "texture_url": texture_url}


# ==============================
# 🎮 마인크래프트 인증 UI 요소들
# ==============================
class VerifyConfirmView(discord.ui.View):
    def __init__(self, mc_name):
        super().__init__(timeout=60)
        self.mc_name = mc_name

    @discord.ui.button(label="✔ 내 계정이 맞습니다 (연동 완료)", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            guild = interaction.guild
            member = interaction.user
            
            # 1. 닉네임 동기화 변경
            await member.edit(nick=self.mc_name)
            
            # 2. 손님 역할 찾기 및 지급 (자동화 추가 ✨)
            role_status_msg = ""
            customer_role = guild.get_role(CUSTOMER_ROLE_ID)
            
            if customer_role:
                await member.add_roles(customer_role)
                role_status_msg = f" 및 **`{customer_role.name}`** 역할이 지급되었습니다."
            else:
                role_status_msg = "되었습니다. (⚠️ 설정된 손님 역할 ID를 서버에서 찾을 수 없습니다.)"

            await interaction.followup.send(
                f"✨ **성공적으로 연동되었습니다!**\n"
                f"디스코드 프로필 닉네임이 `{self.mc_name}`(으)로 변경{role_status_msg}", 
                ephemeral=True
            )
            
        except discord.Forbidden:
            # 역할 지급이나 닉네임 변경 권한이 봇보다 위 계층에 있거나 권한이 부족할 때
            await interaction.followup.send(
                f"⚠️ **프로필 검증은 성공했습니다!**\n"
                f"다만, 봇의 권한 계층이 낮거나 부족하여 닉네임 변경 및 역할 지급을 강제할 수 없습니다.\n"
                f"관리자에게 권한 수정을 요청하시거나, 닉네임을 직접 **`{self.mc_name}`**으로 수정해 주세요.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"❌ 연동 처리 중 오류가 발생했습니다: {str(e)}", ephemeral=True)
        self.stop()


class MCNameModal(discord.ui.Modal, title="마인크래프트 계정 프로필 조회"):
    mc_name_input = discord.ui.TextInput(
        label="마인크래프트 게임 닉네임",
        placeholder="대소문자를 정확하게 입력해 주세요.",
        min_length=3,
        max_length=16,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        username = self.mc_name_input.value
        
        profile = await fetch_minecraft_profile(username)
        if not profile:
            await interaction.followup.send("❌ 존재하지 않거나 올바르지 않은 마인크래프트 정품 닉네임입니다.", ephemeral=True)
            return

        uuid = profile["uuid"]
        real_name = profile["name"]
        texture = profile["texture_url"]

        embed = discord.Embed(
            title="🔒 계정 프로필 본인 검증",
            description="가져온 마인크래프트 정보가 본인 소유가 맞는지 대조해 보세요.\n정보가 일치한다면 아래 **[연동 완료]** 버튼을 눌러주세요.",
            color=discord.Color.from_rgb(47, 49, 54)
        )
        embed.add_field(name="👤 마인크래프트 네임", value=f"`{real_name}`", inline=True)
        embed.add_field(name="🆔 계정 고유 UUID", value=f"`{uuid}`", inline=False)
        
        if texture:
            embed.add_field(name="📂 정품 스킨 원본 리소스", value=f"[텍스처 주소 바로가기]({texture})", inline=False)

        embed.set_thumbnail(url=f"https://visage.surate.cc/bust/128/{uuid}")
        embed.set_image(url=f"https://visage.surate.cc/full/256/{uuid}")
        
        view = VerifyConfirmView(real_name)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


class VerificationInitialView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎮 마인크래프트 계정 연동하기", style=discord.ButtonStyle.secondary, custom_id="persistent_mc_verify_btn")
    async def start_verification(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MCNameModal())


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
# 슬래시 명령어 그룹 (이용금액)
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
            f"✅ 성공적으로 금액을 추가했습니다!\n"
            f"👤 유저: {member.mention}\n"
            f"📈 추가 금액: **{amount:,}원**\n"
            f"💰 총 누적 금액: **{new_amount:,}원**"
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
        
        if new_amount < 0:
            new_amount = 0

        amounts[user_id_str] = new_amount
        
        save_amounts(amounts)
        write_log(interaction.user.name, member.name, amount, new_amount, action="감소됨")

        await interaction.response.send_message(
            f"📉 성공적으로 금액을 차감했습니다!\n"
            f"👤 유저: {member.mention}\n"
            f"📉 차감 금액: **{amount:,}원**\n"
            f"💰 총 누적 금액: **{new_amount:,}원**"
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

        sorted_amounts = sorted(amounts.items(), key=lambda x: x[1], reverse=True)

        msg = "📋 **[전체 이용금액 유저 명단 현황]**\n"
        msg += "──────────────────\n"
        
        for user_id_str, amount in sorted_amounts:
            member = interaction.guild.get_member(int(user_id_str))
            user_mention = member.mention if member else f"서버를 나간 유저 ({user_id_str})"
            msg += f"• {user_mention} 님 ➡️ 💰 **{amount:,}원**\n"
            
        msg += "──────────────────"

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
    bot.add_view(VerificationInitialView())
    
    bot.tree.clear_commands(guild=None)
    bot.tree.add_command(AmountSystem())
    await bot.tree.sync()
    
    print(f"Logged in as {bot.user}")
    print("✅ 슬래시 명령어 동기화 및 마크 역할 지급 모듈 활성화 완료")


# ==============================
# 일반 접두사 명령어 (!)
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

@bot.command(name="DB파일")
async def download_db_files(ctx):
    if ctx.author.id != ADMIN_ID:
        await ctx.send("❌ 총관리자만 사용할 수 있는 보안 명령어입니다.")
        return

    json_path = os.path.join(DATA_DIR, "user_amounts.json")
    log_path = os.path.join(DATA_DIR, "amount_log.txt")
    
    files = []
    
    if os.path.exists(json_path):
        files.append(discord.File(json_path))
    if os.path.exists(log_path):
        files.append(discord.File(log_path))
        
    if files:
        await ctx.send("📂 **[Railway 영구 볼륨 데이터 백업]**\n현재까지 누적된 유저 금액 데이터와 로그 파일입니다.", files=files)
    else:
        await ctx.send("❌ 아직 볼륨 내에 누적된 데이터 파일이 존재하지 않습니다.")

@bot.command(name="인증설정")
async def setup_verification(ctx):
    if ctx.author.id != ADMIN_ID:
        await ctx.send("❌ 총관리자만 사용할 수 있는 명령어입니다.")
        return
        
    embed = discord.Embed(
        title="🎮 계정 연동",
        description=(
            "본 서버는 쾌적하고 투명한 커뮤니티 관리를 위해\n"
            "마인크래프트 정품 계정 연동 시스템을 제공하고 있습니다.\n\n"
            "아래 **[마인크래프트 계정 연동하기]** 버튼을 누른 후 본인의 게임 닉네임을\n"
            "입력해 주시면 확인 후 디스코드 프로필 이름이 자동으로 동기화되며,\n"
            "서버 활동을 위한 **기본 역할이 자동으로 지급**됩니다."
        ),
        color=discord.Color.from_rgb(47, 49, 54)
    )
    embed.set_footer(text="정품 마인크래프트 계정만 연동을 지원합니다.")
    
    await ctx.send(embed=embed, view=VerificationInitialView())

# ==============================
# 실행
# ==============================
bot.run(TOKEN)
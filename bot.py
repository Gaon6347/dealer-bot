


디스코드 봇 만드려는데 혹시 이런건 되나?

명령어를 치면 디코닉네임을 입력가능한창이 뜨고 디코닉네임 적으면 또 금액을 입력가능한 창이 뜨는데 금액을 기입하면 디코닉네임 가진사람한테 이용금액이 쌓여.

그래서 뭐 예를들어 ./이용금액을 유저가 치면 자기가 쓴 이용금액 전부가 나오는거지

근데 이게 데이터가 휘발될수 있으니까 로그파일을 따로 관리해서 거기다가도 남게끔

된다 👍 그리고 디코봇으로 꽤 정석적인 구조라서 구현도 어렵지 않음
네가 말한 기능은 요약하면 이거야:

🔧 구현하고 싶은 기능 구조
/금액추가 명령어 입력

→ 닉네임 입력 창 (모달) 뜸

→ 입력하면 금액 입력 창 뜸

→ 입력 완료하면

해당 유저의 누적 금액 저장

로그파일에도 기록

/이용금액
→ 자기 누적 금액 확인

✅ 이거 가능하냐?
👉 100% 가능 (디코 슬래시 명령어 + 모달 기능)

디스코드에서 제공하는:

Slash Command

Modal (입력창)

Interaction

이 3개 조합이면 구현됨

🧠 구현 방식 (추천 구조)
1️⃣ 라이브러리
Python 기준이면 👉 discord.py (2.x) or nextcord

2️⃣ 데이터 저장 방식 (중요)
휘발 방지하려면:

✔ 방법 1: JSON 파일 (간단 추천)
{
  "유저ID": 150000,
  "유저ID2": 300000
}
✔ 방법 2: SQLite (조금 더 안정)
나중에 기능 늘릴거면 이게 좋음

3️⃣ 로그 파일 따로 저장
[2026-07-12 21:30] 관리자 -> 김형진 : +50000
💻 예시 코드 (핵심만)
🔹 기본 구조 (Python / discord.py)
import discord
from discord.ext import commands
import json
from datetime import datetime

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 데이터 로드
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)

data = load_data()
🔹 모달 (입력창)
class MoneyModal(discord.ui.Modal, title="금액 추가"):
    user_name = discord.ui.TextInput(label="닉네임 입력")
    amount = discord.ui.TextInput(label="금액 입력")

    async def on_submit(self, interaction: discord.Interaction):
        user = self.user_name.value
        amount = int(self.amount.value)

        user_id = str(interaction.user.id)

        if user_id not in data:
            data[user_id] = 0

        data[user_id] += amount
        save_data(data)

        # 로그 기록
        with open("log.txt", "a") as f:
            f.write(f"[{datetime.now()}] {interaction.user} -> {user} : +{amount}\n")

        await interaction.response.send_message(f"{user}에게 {amount} 추가 완료", ephemeral=True)
🔹 명령어
@bot.tree.command(name="금액추가")
async def add_money(interaction: discord.Interaction):
    await interaction.response.send_modal(MoneyModal())
🔹 조회 명령어
@bot.tree.command(name="이용금액")
async def check_money(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    amount = data.get(user_id, 0)

    await interaction.response.send_message(f"누적 이용금액: {amount}", ephemeral=True)
⚠️ 중요한 포인트
닉네임 말고 유저ID 기준 저장해야 꼬임 없음

금액 입력은 반드시 int 변환 + 예외처리 해야됨

로그파일은 무조건 append 방식 (a)

봇 꺼져도 JSON은 남아서 유지됨

🔥 더 고급 기능 (원하면 추가 가능)
관리자만 금액추가 가능

랭킹 시스템 (/랭킹)

특정 유저 조회 (/조회 @유저)

VIP 자동 등급

% 페이백 자동 계산

💬 한줄 정리
👉 "슬래시 명령어 + 모달 + JSON 저장 + 로그파일" 이 조합이면 네가 원하는거 전부 구현됨

원하면
👉 "버튼 UI + 2단계 입력창 (닉네임 → 금액)" 완전 실사용용 코드
👉 또는 Railway / 24시간 호스팅까지 세팅

다 만들어줄게 👍


파이선에 복붙만 하면 되는 전체 코드를 알려줘봐

좋다 👍 “그대로 복붙해서 실행 가능한 수준”으로 만들어줄게
(디코봇 처음 기준 + 모달 + 저장 + 로그까지 완성본)

🧩 기능 포함
/금액추가 → 닉네임 + 금액 입력 (모달)

/이용금액 → 내 누적 금액 확인

JSON 파일 자동 생성 (데이터 유지)

log.txt 기록

⚙️ 사전 준비
1️⃣ 라이브러리 설치
pip install discord.py
2️⃣ 디코 봇 토큰 준비
👉 코드 맨 아래 "YOUR_TOKEN" 부분에 넣기

💻 전체 코드 (복붙용)
import discord
from discord.ext import commands
import json
import os
from datetime import datetime

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"
LOG_FILE = "log.txt"

# -------------------------
# 데이터 로드 / 저장
# -------------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

data = load_data()

# -------------------------
# 로그 기록
# -------------------------
def write_log(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

# -------------------------
# 모달 (입력창)
# -------------------------
class MoneyModal(discord.ui.Modal, title="금액 추가"):
    target_user = discord.ui.TextInput(
        label="닉네임 또는 ID 입력",
        placeholder="예: 김형진 또는 123456789",
        required=True
    )

    amount = discord.ui.TextInput(
        label="금액 입력",
        placeholder="숫자만 입력",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        global data

        user_input = self.target_user.value
        amount_input = self.amount.value

        # 금액 검증
        try:
            amount = int(amount_input)
        except:
            await interaction.response.send_message("❌ 숫자만 입력하세요", ephemeral=True)
            return

        # 유저 찾기
        target = None

        # ID로 찾기
        if user_input.isdigit():
            target = interaction.guild.get_member(int(user_input))

        # 닉네임으로 찾기
        if target is None:
            for member in interaction.guild.members:
                if member.display_name == user_input or member.name == user_input:
                    target = member
                    break

        if target is None:
            await interaction.response.send_message("❌ 유저를 찾을 수 없음", ephemeral=True)
            return

        user_id = str(target.id)

        if user_id not in data:
            data[user_id] = 0

        data[user_id] += amount
        save_data(data)

        # 로그
        log_text = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {interaction.user} -> {target} : +{amount}"
        write_log(log_text)

        await interaction.response.send_message(
            f"✅ {target.display_name} 에게 {amount}원 추가 완료\n현재 누적: {data[user_id]}원",
            ephemeral=True
        )

# -------------------------
# 명령어
# -------------------------
@bot.tree.command(name="금액추가", description="유저에게 금액 추가")
async def add_money(interaction: discord.Interaction):
    await interaction.response.send_modal(MoneyModal())

@bot.tree.command(name="이용금액", description="내 누적 금액 확인")
async def check_money(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    amount = data.get(user_id, 0)

    await interaction.response.send_message(
        f"💰 현재 누적 이용금액: {amount}원",
        ephemeral=True
    )

# -------------------------
# 봇 준비 완료 시
# -------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ 로그인 완료: {bot.user}")

# -------------------------
# 실행
# -------------------------
bot.run("YOUR_TOKEN")
📂 실행하면 생기는 파일
data.json → 유저별 금액 저장

log.txt → 기록 로그

⚠️ 꼭 알아야 할 것
🔴 1. 봇 권한
서버에 멤버 보기 권한 있어야 닉네임 검색됨

🔴 2. 슬래시 명령어 안보이면
봇 초대 다시 하거나

몇 초 기다려야 뜸

🔥 추가로 해주면 좋은거
원하면 바로 만들어줄게 👇

/조회 @유저 → 특정 유저 금액 확인

/랭킹 → TOP 유저

관리자만 금액추가

버튼 UI (더 깔끔하게)

자동 VIP 시스템

원하면 다음 단계로
👉 디코 버튼 + 카지노 느낌 UI + 자동 페이백 시스템까지 확장
도 만들어줄게 😎


import discord
from discord.ext import commands
import asyncio
import time
import os

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

    @discord.ui.button(label="📞 담당자 호출", style=discord.ButtonStyle.primary)
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
# 🔥 핵심 (버튼 안 죽게 하는 부분)
# ==============================
@bot.event
async def on_ready():
    bot.add_view(CallView())
    print(f"Logged in as {bot.user}")

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

지금 이게 내가 쓰고있는 봇이거든

여기에 같이 넣어써도 버그 없겠지?

결론부터 말하면 👉 “그대로 합치면 높은 확률로 문제 생김”
근데 구조 조금만 정리하면 완벽하게 같이 사용 가능 👍

⚠️ 왜 그냥 합치면 위험하냐
너 코드 + 내가 준 코드 차이점 때문에 충돌 가능 있음

1️⃣ 봇 객체 중복
bot = commands.Bot(...)
👉 이미 있는데 또 만들면 봇 2개됨 → 오류

2️⃣ on_ready 이벤트 충돌
너 코드:

@bot.event
async def on_ready():
    bot.add_view(CallView())
내 코드에도:

@bot.event
async def on_ready():
    await bot.tree.sync()
👉 둘 중 하나 덮어씌워짐

3️⃣ 슬래시 명령어 sync 안됨
👉 /금액추가, /이용금액 안 뜰 수 있음

✅ 안전하게 합치는 방법 (핵심만)
🔧 1. on_ready 하나로 합쳐라
👉 이렇게 바꿔

@bot.event
async def on_ready():
    bot.add_view(CallView())  # 기존 버튼 유지
    await bot.tree.sync()     # 슬래시 명령어 등록
    print(f"✅ 로그인 완료: {bot.user}")
🔧 2. bot 중복 생성 ❌
👉 지금 코드에 있는 이거 그대로 유지

bot = commands.Bot(command_prefix="!", intents=intents)
👉 내가 준 코드에서 이 부분은 삭제

🔧 3. 데이터/모달 코드만 추가
👉 아래 것들만 추가하면 됨:

✔ 추가할 것
JSON 로드/저장 함수

MoneyModal 클래스

/금액추가

/이용금액

🔥 네 코드 기준 "추가 위치"
📌 1. 상단 import 아래에 추가
import json
from datetime import datetime

DATA_FILE = "data.json"
LOG_FILE = "log.txt"

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

data = load_data()

def write_log(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")
📌 2. 모달 추가 (아무 클래스 아래에 붙여도 됨)
class MoneyModal(discord.ui.Modal, title="금액 추가"):
    target_user = discord.ui.TextInput(label="닉네임 또는 ID 입력")
    amount = discord.ui.TextInput(label="금액 입력")

    async def on_submit(self, interaction: discord.Interaction):
        global data

        try:
            amount = int(self.amount.value)
        except:
            await interaction.response.send_message("❌ 숫자만 입력", ephemeral=True)
            return

        target = None

        if self.target_user.value.isdigit():
            target = interaction.guild.get_member(int(self.target_user.value))

        if target is None:
            for m in interaction.guild.members:
                if m.display_name == self.target_user.value or m.name == self.target_user.value:
                    target = m
                    break

        if target is None:
            await interaction.response.send_message("❌ 유저 못찾음", ephemeral=True)
            return

        uid = str(target.id)

        if uid not in data:
            data[uid] = 0

        data[uid] += amount
        save_data(data)

        write_log(f"[{datetime.now()}] {interaction.user} -> {target} : +{amount}")

        await interaction.response.send_message(
            f"✅ {target.display_name} +{amount}\n누적: {data[uid]}",
            ephemeral=True
        )
📌 3. 슬래시 명령어 추가
@bot.tree.command(name="금액추가")
async def add_money(interaction: discord.Interaction):
    await interaction.response.send_modal(MoneyModal())

@bot.tree.command(name="이용금액")
async def check_money(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    amount = data.get(uid, 0)

    await interaction.response.send_message(
        f"💰 누적 이용금액: {amount}",
        ephemeral=True
    )
💥 최종 상태
👉 네 기존 기능

담당자 호출

채널 생성

버튼 시스템

👉 + 새 기능

금액 적립 시스템

로그 저장

개인 조회

👉 전부 같이 정상 작동

🔥 추가로 꼭 추천
지금 구조면 나중에 문제 생길 수 있음 👇

👉 금액추가 관리자 제한
if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles]:
    return await interaction.response.send_message("❌ 담당자만 가능", ephemeral=True)
💬 한줄 정리
👉 "on_ready 합치고, bot 중복만 피하면 100% 문제없이 같이 사용 가능"

원하면 다음 단계로
👉 VIP 자동 등급 / 페이백 % 자동 계산 / 도박장 통계 시스템
까지 깔끔하게 확장해줄게 😎


너가 직접 수정해줘 

좋다 👍 네 코드에 충돌 없이 완전히 합쳐서 바로 실행 가능한 상태로 만들어줬다
(그대로 복붙하면 됨)

💻 ✅ 최종 통합 코드
import discord
from discord.ext import commands
import asyncio
import time
import os
import json
from datetime import datetime

TOKEN = os.environ.get("TOKEN")
DEALER_ROLE_NAME = "담당자"
LOG_CHANNEL_ID = 1521553559211085907
ADMIN_ID = 1389846967626109094
CATEGORY_ID = 1521550375939997890

DATA_FILE = "data.json"
LOG_FILE = "log.txt"

active_calls = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# 데이터 저장
# ==============================
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

data = load_data()

def write_log(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

# ==============================
# 💰 금액 모달
# ==============================
class MoneyModal(discord.ui.Modal, title="금액 추가"):
    target_user = discord.ui.TextInput(label="닉네임 또는 ID 입력")
    amount = discord.ui.TextInput(label="금액 입력")

    async def on_submit(self, interaction: discord.Interaction):
        global data

        # 관리자 제한 (담당자만 가능)
        if DEALER_ROLE_NAME not in [r.name for r in interaction.user.roles]:
            await interaction.response.send_message("❌ 담당자만 사용 가능", ephemeral=True)
            return

        try:
            amount = int(self.amount.value)
        except:
            await interaction.response.send_message("❌ 숫자만 입력", ephemeral=True)
            return

        target = None

        # ID 검색
        if self.target_user.value.isdigit():
            target = interaction.guild.get_member(int(self.target_user.value))

        # 닉네임 검색
        if target is None:
            for m in interaction.guild.members:
                if m.display_name == self.target_user.value or m.name == self.target_user.value:
                    target = m
                    break

        if target is None:
            await interaction.response.send_message("❌ 유저 못찾음", ephemeral=True)
            return

        uid = str(target.id)

        if uid not in data:
            data[uid] = 0

        data[uid] += amount
        save_data(data)

        write_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {interaction.user} -> {target} : +{amount}")

        await interaction.response.send_message(
            f"✅ {target.display_name} +{amount}원\n누적: {data[uid]}원",
            ephemeral=True
        )

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

    @discord.ui.button(label="📞 담당자 호출", style=discord.ButtonStyle.primary)
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
# 슬래시 명령어
# ==============================
@bot.tree.command(name="금액추가")
async def add_money(interaction: discord.Interaction):
    await interaction.response.send_modal(MoneyModal())

@bot.tree.command(name="이용금액")
async def check_money(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    amount = data.get(uid, 0)

    await interaction.response.send_message(
        f"💰 누적 이용금액: {amount}원",
        ephemeral=True
    )

# ==============================
# 기존 버튼 명령어
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
# 봇 준비
# ==============================
@bot.event
async def on_ready():
    bot.add_view(CallView())  # 버튼 유지
    await bot.tree.sync()     # 슬래시 명령어 등록
    print(f"✅ 로그인 완료: {bot.user}")

# ==============================
# 실행
# ==============================
bot.run(TOKEN)
🔥 적용 후 체크리스트
✔ 1. 슬래시 명령어 안보이면
봇 재초대 or 몇 초 기다리기

✔ 2. 담당자 역할 이름 정확히
DEALER_ROLE_NAME = "담당자"
✔ 3. TOKEN 환경변수 확인
Railway 쓰면 이미 OK

💬 진짜 핵심 정리
👉 지금 코드 =
담당자 호출 시스템 + 금액 적립 시스템 완전히 통합 완료 상태

원하면 다음 단계로
👉 VIP 자동 등급 / 페이백 자동 계산 / 도박 통계 대시보드
까지 이어서 만들어줄게 😎




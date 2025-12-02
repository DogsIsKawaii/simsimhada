import os
import asyncio
import requests
import random
import discord
from discord import app_commands

# ----------------------------------
# 환경 변수에서 토큰 가져오기
# ----------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")

# ----------------------------------
# 사용을 허용할 디스코드 서버(길드) ID
# ----------------------------------
ALLOWED_GUILD_ID = 1316677392517042237  # 서버 ID

def is_allowed_guild(interaction: discord.Interaction) -> bool:
    """이 상호작용이 허용된 서버에서 온 것인지 확인"""
    return interaction.guild is not None and interaction.guild.id == ALLOWED_GUILD_ID

# ----------------------------------
# 가격/포맷 관련 함수
# ----------------------------------

# BTC 가격 가져오기 (업비트 KRW-BTC)
def get_btc_price():
    url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    return requests.get(url).json()[0]["trade_price"]

# 원화 포맷 함수 (예: 1234567.0 → "1,234,567.0")
def format_krw(amount: float) -> str:
    formatted = f"{amount:,.2f}"
    if formatted.endswith("00"):
        formatted = f"{amount:,.1f}"
    return formatted

# bitcoin 관련 상수/함수
# 1 BTC = 100,000,000 bitcoin (₿100,000,000 또는 1 BTC)
# 입력은 정수 bitcoin 단위로 받고, 내부에서는 BTC로 변환해서 계산
BITCOIN_PER_BTC = 100_000_000  # 1 BTC = 100,000,000 bitcoin (₿100,000,000 또는 1 BTC)

def btc_to_units(btc: float) -> int:
    """BTC 값을 정수 bitcoin 단위로 변환"""
    return int(btc * BITCOIN_PER_BTC)

def format_bitcoin_units(units: int) -> str:
    """정수 bitcoin 수량을 3자리마다 콤마 넣어서 문자열로 포맷"""
    return f"{units:,}"

def format_premium(p: float) -> str:
    """프리미엄/할인 표기용 문자열 생성
       - p < 0  → 할인
       - p >= 0 → 프리미엄 (0도 프리미엄으로 표기)
    """
    if p < 0:
        return f"할인 {abs(p):.2f}%"
    else:
        return f"프리미엄 {p:.2f}%"

# ----------------------------------
# 랜덤 인스피레이션(영감을 주는 문장) 리스트
# ----------------------------------
INSPIRATION_MESSAGES = [
    "📜 Inspiration 1\n만약 당신이 믿지 않거나 이해하지 못한다면, 설득할 시간이 없습니다. -사토시 나카모토-",
    "📜 Inspiration 2\n은행이 필요 없는 새로운 전자 화폐 -비트코인 백서 중-",
    "📜 Inspiration 3\nThe Times 2009년 1월 3일, 총리, 두 번째 은행 구제금융 직전 -비트코인 제네시스 블록 메시지-",
    "📜 Inspiration 4\n두 번째로 좋은 것은 없다. -마이클 세일러-",
    "📜 Inspiration 5\n사람들은 자신에게 합당한 가격에 비트코인을 가진다. -마이클 세일러-",
    "📜 Inspiration 6\n겸손함을 유지하고 비트코인을 꾸준히 모아라. -비트코인과 관련된 명언-",
    "📜 Inspiration 7\n네 키가 아니면, 네 비트코인이 아니다. -비트코인과 관련된 명언-",
    "📜 Inspiration 8\n비트코인: 개인 대 개인 전자화폐 시스템. -비트코인 백서 제목-",
    "📜 Inspiration 9\n비트코인의 첫 배포를 알립니다. -사토시 나카모토, 경화가 탄생하는 순간-",
    "📜 Inspiration 10\n기존 통화의 근본적인 문제는 시스템이 돌아가도록 하는 데 신뢰가 필요하다는 점입니다. -사토시 나카모토-",
    "📜 Inspiration 11\n언제 일어날지 모르는 중앙 관리형 통화의 인플레이션 리스크에서 탈출하세요! -사토시 나카모토-",
    "📜 Inspiration 12\n그러니까 비트코인을 갖기 않는 것이 진짜 낭비인 것이죠. -사토시 나카모토-",
    "📜 Inspiration 13\n저는 제가 남긴 유산이 마음에 듭니다. -할피니-",
    "📜 Inspiration 14\n비트코인 시스템을 제대로 설명할 수만 있다면 자유주의자들이 꽤나 솔깃하게 생각할 것입니다. -사토시 나카모토-",
    # 여기다가 원하는 문장 계속 추가해도 됨
]

# ----------------------------------
# 디스코드 봇 클래스
# ----------------------------------
class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.status_task = None

    async def setup_hook(self):
        # 봇이 준비되면 상태창 업데이트 루프 시작
        self.status_task = asyncio.create_task(self.update_status_loop())

    async def on_ready(self):
        print(f"{self.user} 로그인 완료!")
        await self.tree.sync()
        print("슬래시 명령어 등록 완료")

    async def update_status_loop(self):
        # 봇이 완전히 준비될 때까지 대기
        await self.wait_until_ready()
        while not self.is_closed():
            price = get_btc_price()
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"BTC {format_krw(price)}원 (업비트 기준)"
                )
            )
            await asyncio.sleep(60)  # 1분마다 업데이트

bot = MyBot()

# ----------------------------------
# 슬래시 명령어
# ----------------------------------

# /btc : 현재 BTC 시세 (원화)
@bot.tree.command(name="btc", description="현재 비트코인 시세를 조회합니다.")
async def btc(interaction: discord.Interaction):
    if not is_allowed_guild(interaction):
        await interaction.response.send_message(
            "이 봇은 지정된 서버에서만 사용할 수 있어요.",
            ephemeral=True
        )
        return

    price = get_btc_price()
    await interaction.response.send_message(
        f"💰 현재 비트코인 가격: {format_krw(price)}원",
        ephemeral=True
    )

# /to_krw : bitcoin(정수) → 원화 변환
@bot.tree.command(name="to_krw", description="bitcoin 단위를 원화로 변환합니다.")
@app_commands.describe(
    amount="bitcoin 수량 (예: 2100)",
    premium="프리미엄 % (음수 입력 시 할인)"
)
async def to_krw(
    interaction: discord.Interaction,
    amount: int,              # 정수 bitcoin 단위
    premium: float = 0.0      # 기본값 0
):
    if not is_allowed_guild(interaction):
        await interaction.response.send_message(
            "이 봇은 지정된 서버에서만 사용할 수 있어요.",
            ephemeral=True
        )
        return

    price = get_btc_price()

    # 정수 bitcoin → BTC
    btc_amount = amount / BITCOIN_PER_BTC

    krw = btc_amount * price
    krw_with_premium = krw * (1 + premium / 100)

    await interaction.response.send_message(
        f"₿{format_bitcoin_units(amount)} → 💵 {format_krw(krw_with_premium)} 원 "
        f"({format_premium(premium)})",
        ephemeral=True
    )

# /to_btc : 원화 → bitcoin(정수) 변환
@bot.tree.command(name="to_btc", description="원화를 bitcoin 단위로 변환합니다.")
@app_commands.describe(
    amount="원화 금액",
    premium="프리미엄 % (음수 입력 시 할인)"
)
async def to_btc(
    interaction: discord.Interaction,
    amount: float,            # 원화 금액
    premium: float = 0.0      # 기본값 0
):
    if not is_allowed_guild(interaction):
        await interaction.response.send_message(
            "이 봇은 지정된 서버에서만 사용할 수 있어요.",
            ephemeral=True
        )
        return

    price = get_btc_price()

    # 원화 → BTC
    btc = amount / price
    btc_with_premium = btc / (1 + premium / 100)

    # BTC → 정수 bitcoin 단위
    units = btc_to_units(btc_with_premium)

    await interaction.response.send_message(
        f"💵 {format_krw(amount)} 원 → ₿{format_bitcoin_units(units)} "
        f"({format_premium(premium)})",
        ephemeral=True
    )

# ✅ /inspiration : 오렌지 홀릭을 채워줄 단어를 랜덤 출력합니다.
@bot.tree.command(name="inspiration", description="랜덤 인스피레이션(어록)을 출력합니다.")
async def inspiration(interaction: discord.Interaction):
    if not is_allowed_guild(interaction):
        await interaction.response.send_message(
            "이 봇은 지정된 서버에서만 사용할 수 있어요.",
            ephemeral=True
        )
        return

    message = random.choice(INSPIRATION_MESSAGES)
    await interaction.response.send_message(message, ephemeral=True)

# ----------------------------------
# 봇 실행
# ----------------------------------
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN 환경 변수가 설정되지 않았습니다.")

bot.run(TOKEN)

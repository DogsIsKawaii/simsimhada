import os
import asyncio
import requests
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
# amount는 정수 bitcoin, premium은 기본값 0 (입력 안 하면 0으로 계산)
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
# premium은 기본값 0 (입력 안 하면 0으로 계산)
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

# ----------------------------------
# 봇 실행
# ----------------------------------
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN 환경 변수가 설정되지 않았습니다.")

bot.run(TOKEN)

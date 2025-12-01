import os
import asyncio
import requests
import discord
from discord import app_commands

# ----------------------------------
# 환경 변수에서 토큰 가져오기
# ----------------------------------
TOKEN = os.getenv("DISCORD_TOKEN")

# BTC 가격 가져오기
def get_btc_price():
    url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    return requests.get(url).json()[0]["trade_price"]

# 원화 포맷 함수
def format_krw(amount):
    formatted = f"{amount:,.2f}"
    if formatted.endswith("00"):
        formatted = f"{amount:,.1f}"
    return formatted

# BTC 포맷 함수
def format_btc(amount):
    return f"{amount:.8f}"

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
        await self.wait_until_ready()
        while not self.is_closed():
            price = get_btc_price()
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"BTC {format_krw(price)}원 (업비트 기준)"
                )
            )
            await asyncio.sleep(10)

bot = MyBot()

# ----------------------------------
# 슬래시 명령어
# ----------------------------------

# /btc : 현재 BTC 시세
@bot.tree.command(name="btc", description="현재 비트코인 시세를 조회합니다.")
async def btc(interaction: discord.Interaction):
    price = get_btc_price()
    await interaction.response.send_message(
        f"💰 현재 비트코인 가격: {format_krw(price)}원",
        ephemeral=True
    )

# /to_krw : BTC → 원화 변환 (프리미엄 옵션)
@bot.tree.command(name="to_krw", description="BTC를 원화로 변환합니다.")
@app_commands.describe(amount="BTC 수량", premium="프리미엄 % (선택, 기본 0.0)")
async def to_krw(interaction: discord.Interaction, amount: float, premium: float = 0.0):
    price = get_btc_price()
    krw = amount * price
    krw_with_premium = krw * (1 + premium / 100)
    await interaction.response.send_message(
        f"₿ {format_btc(amount)} BTC → 💵 {format_krw(krw_with_premium)} 원 "
        f"(프리미엄 {premium:+.2f}%)",
        ephemeral=True
    )

# /to_btc : 원화 → BTC 변환 (프리미엄 옵션)
@bot.tree.command(name="to_btc", description="원화를 BTC로 변환합니다.")
@app_commands.describe(amount="원화 금액", premium="프리미엄 % (선택, 기본 0.0)")
async def to_btc(interaction: discord.Interaction, amount: float, premium: float = 0.0):
    price = get_btc_price()
    btc = amount / price
    btc_with_premium = btc / (1 + premium / 100)
    await interaction.response.send_message(
        f"💵 {format_krw(amount)} 원 → ₿ {format_btc(btc_with_premium)} BTC "
        f"(프리미엄 {premium:+.2f}%)",
        ephemeral=True
    )

# ----------------------------------
# 봇 실행
# ----------------------------------
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN 환경 변수가 설정되지 않았습니다.")

bot.run(TOKEN)

import os  # default module
import discord
from discord.ext import commands
from discord.ui import view
from dotenv import load_dotenv
import subprocess
import json
import shutil

load_dotenv()  # load all the variables from the env file
bot = discord.Bot()

count = 0
path = ""


@bot.event
async def on_connect():
    if bot.auto_sync_commands:
        await bot.sync_commands()
    print(f"{bot.user} connected.")

# 관리자 가능
async def GetDoTypes(ctx: discord.AutocompleteContext):
  getTypes = ctx.options['do']
  if getTypes == '프리미엄':
    return ['활성화', '비활성화']
  elif getTypes == '회원':
    return ['차단', '해제', "보기"]
  elif getTypes == '역할':
    return ['소유자', '관리자', '유저']

@bot.slash_command(name="유저관리", description="JSON에 등록된 유저를 관리합니다.")
async def ManageUser(ctx: discord.ApplicationContext,
                     user: discord.Member,
                     do: discord.Option(str, choices=["프리미엄", "회원", "역할"]),
                     actions: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(GetDoTypes))):
    with open("userInfo.json", "r") as f:
        json_data = json.load(f)
        me = json_data[str(ctx.author.id)]
        you = json_data[str(user.id)]
    try:
        if me["role"] == "admin" or me["role"] == "manager":
            if actions == "활성화":
                you["isPremium"] = True
            elif actions == "비활성화":
                you["isPremium"] = False
            elif actions == "차단":
                you["isBlock"] = True
            elif actions == "해제":
                you["isBlock"] = False
            elif actions == "보기":
                await ctx.respond(you, ephemeral=True)
                return
            elif actions == "소유자":
                you["role"] = "admin"
            elif actions == "관리자":
                you["role"] = "manager"
            elif actions == "유저":
                you["role"] = "user"
            
            with open("userInfo.json", "w") as outfile:
                json.dump(json_data, outfile, indent=4)
            await ctx.respond("셋팅이 완료되었습니다!", ephemeral=True)
        else:
            await ctx.respond("관리자 권한이 아닙니다!", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"오류 발생!\n{e}", ephemeral=True)
    
# 유저 기능
@bot.slash_command(
    name="스티커변환", description="동영상 파일을 GIF 혹은 PNG로 내보냅니다"
)
async def StickerConvert(
    ctx: discord.ApplicationContext,
    video: discord.Attachment,
    extension: discord.Option(str, choices=["GIF", "PNG"]),
):

    if VaildUser(ctx.author.id) == False:
        view = MyView()
        view.add_item(
            discord.ui.Button(
                label="이용 약관 보기",
                style=discord.ButtonStyle.link,
                url="https://www.naver.com", # TODO: 약관 개정
            )
        )
        embed = discord.Embed(
            title="회원 등록이 필요합니다!",
            description="다양한 서비스를 이용하려면 최초 1회 등록이 필요합니다. 아래 버튼을 누르면 이용약관에 동의합니다.",
        )
        await ctx.respond(embed=embed, view=view, ephemeral=True)
    else:
        try:
            print(VaildUser(ctx.author.id))
            if not VaildUser(ctx.author.id) == "prohibit":
                await ctx.defer()  # 15초 지연
                await ctx.respond("처리 중입니다!", ephemeral=True)
                await ctx.respond(
                    f"{ctx.author.mention}",
                    file=FileProcess(video, extension),
                    ephemeral=True,
                )
                os.remove(path)
            else:
                await ctx.respond("당신은 이 서비스에 대한 부적격자로 서비스를 이용할 수 없습니다!\n자세한 사항은 지원팀에 문의 부탁드립니다.", ephemeral=True)
        except Exception as e:
            await ctx.respond(f"Error : {e}", ephemeral=True)
            os.remove(path)


class MyView(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="동의", style=discord.ButtonStyle.success)
    async def first_button_callback(self, button, interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            """회원가입이 완료되었습니다!
            서비스 이용이 가능합니다.""", ephemeral=True
        )
        AddId(interaction.user.id)

    @discord.ui.button(label="거절", style=discord.ButtonStyle.danger)
    async def second_button_callback(self, button, interaction):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            """
            회원가입이 거부되었습니다!
            서비스를 계속 이용하시려면 동의가 필요합니다.
            """,
            ephemeral=True,
        )


def AddId(id):
    with open("userInfo.json", "r") as f:
        json_data = json.load(f)

        json_data[str(id)] = {"role": "user", "isRegister": True, "isBlock": False, "isPremium": False}

    with open("userInfo.json", "w") as outfile:
        json.dump(json_data, outfile, indent=4)


def VaildUser(userId):
    try:
        with open("userInfo.json", "r") as f:
            json_data = json.load(f)
            vaildUserInfo = json_data[str(userId)]["isRegister"]
            if json_data[str(userId)]["isBlock"] == True:
                return "prohibit"
            else:
                return vaildUserInfo
        
    except Exception as e:
        return False


def FileProcess(video, ext):
    global count
    global path
    count = count + 1
    size = "0x0"
    isVaild = False

    # GIF 변환

    if ext == "GIF":

        path = f"result/{count}.gif"

        if os.path.exists(path):
            os.remove(path)

        for i in range(0, 4):

            if i == 0:
                size = "200"
            if i == 1:
                size = "160"
            if i == 2:
                size = "120"
            if i == 3:
                size = "100"

            command = [          
                "ffmpeg",
                "-y",
                "-i", video.url,
                "-filter_complex",
                f"scale={size}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=256[p];[s1][p]paletteuse=dither=bayer:bayer_scale=3",
                path
            
            ]

            subprocess.run(command, check=True)

            print()
            print(os.path.getsize(path))
            print()

            if os.path.getsize(path) <= 524287:
                isVaild = True
                break

        if not isVaild:
            raise Exception(
                "해당 비디오는 스티커로 변환이 불가능합니다.\n사유 : 입력한 비디오가 너무 큽니다.\n해결방법 : 영상 길이를 줄여주세요."
            )

        file = discord.File(path)

        return file

    # PNG 변환

    if ext == "PNG":

        size = "0:0"
        path = f"result/{count}.png"

        if os.path.exists(path):
            os.remove(path)

        for i in range(0, 4):

            if i == 0:
                size = "200:200"
            if i == 1:
                size = "160:160"
            if i == 2:
                size = "120:120"
            if i == 3:
                size = "100:100"

            command = [
                "ffmpeg",
                "-i",
                video.url,
                "-vf",
                f"scale={size},select=gt(n\,0)",
                "-vframes",
                "1",  # 1프레임만 추출
                "-compression_level",
                "0",  # 무손실 PNG 압축 설정
                "-y",
                path,  # 저장 경로 지정
            ]

            subprocess.run(command, check=True)

            if os.path.getsize(path) <= 524287:
                isVaild = True
                break

        if not isVaild:
            raise Exception(
                "해당 비디오는 스티커로 변환이 불가능합니다.\n사유 : 입력한 비디오가 너무 큽니다.\n해결방법 : 영상 길이를 줄여주세요."
            )

        file = discord.File(path)

        return file

@bot.slash_command(name="지원", description="서포트 서버 초대 링크를 보냅니다.")
async def support(ctx):
    embed=discord.Embed(title="서포트 링크", url="https://discord.gg/SxNJgprFyq", description="윗 링크를 누르시면 서포트 서버로 이동됩니다.", color=0x0ae6e2)
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1132242359107719168/1307966204564078622/1731906746667.png?ex=673ce2b4&is=673b9134&hm=02e18d47f7dfdc998f021c09b3d056ffc3142aeab89d6117b25e25b92a9fc088&=&format=webp&quality=lossless")
    await ctx.respond(embed=embed, ephemeral=True)

@bot.slash_command(name="도움말", description="봇 사용 방법 혹은 약관, 개인정보 처리방침을 확인합니다.")
async def help(ctx):
    embed=discord.Embed(title="도움말 링크", url="https://dull-risk-62c.notion.site/1422746f03df806f8f8ec11fac7e1c6d?pvs=74", description="윗 링크를 누르시면 도움말로 이동됩니다.", color=0x0ae6e2)
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/1132242359107719168/1307966204564078622/1731906746667.png?ex=673ce2b4&is=673b9134&hm=02e18d47f7dfdc998f021c09b3d056ffc3142aeab89d6117b25e25b92a9fc088&=&format=webp&quality=lossless")
    await ctx.respond(embed=embed, ephemeral=True)

bot.run(os.getenv("TOKEN"))  # run the bot with the token

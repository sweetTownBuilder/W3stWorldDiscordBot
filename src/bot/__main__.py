import asyncio
import logging
import random

import discord
from discord.ext import commands

from src.agent.client import Dify
from src.configuration import conf

channels_states = {}

"""启动 bot 并监听消息"""
intents = discord.Intents.default()
intents.members = True  # 允许监听成员加入事件
intents.messages = True  # 允许监听消息事件
intents.guilds = True
intents.message_content = True  # 需要启用以监听消息

bot = commands.Bot(command_prefix="!", intents=intents)
dify: Dify = Dify(conf.dify.api_key, conf.dify.base_url)


# 监听机器人启动
@bot.event
async def on_ready():
    print(f">>> Bot 已登录为：{bot.user} <<<")
    bot.loop.create_task(periodic_message_task())

    # 添加主动发送命令


@bot.command(name='send')
@commands.has_permissions(administrator=True)
async def send_message(ctx, channel_id: int, *, message: str):
    target_channel = bot.get_channel(channel_id)
    if target_channel:
        await target_channel.send(message)
        await ctx.send(f"✅ 消息已发送至 {target_channel.mention}")
    else:
        await ctx.send("❌ 频道不存在")


async def periodic_message_task():
    await bot.wait_until_ready()
    channel = bot.get_channel(conf.bot.channel_id)
    while not bot.is_closed():
        if channel:
            async with channel.typing():
                response = await dify.send_streaming_chat_message(
                    message="Tell a piece of trending news in the field of crypto memecoins，preferably news about a "
                            "price of a memecoin went up trenmendously or someone make a huge returns on a memcoin. "
                            "News should have a clear and specific protagonist, not a general study f the field. If "
                            "appropriate, you may end with a suggestion about what people should do upon hearing the "
                            "news.",
                    user_id=conf.bot.channel_id,
                    conversation_id=None,
                    discord_chat_type = "ask_for_news",
                )
                await channel.send(response.message)
        await asyncio.sleep(random.randint(60 * 60 * 3, 60 * 60 * 5))  # Sleep for a random 5-6 hours


# 当新成员加入时，发送欢迎并@新成员
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        # 这里使用 member.mention 来@该用户
        response = await dify.send_streaming_chat_message(
            message="new member join the group",
            user_id=member.author.id,
            conversation_id=None,
            new_member_name=member.mention,
            user_name=member.mention,
            discord_chat_type="welcome",
        )
        if response.need_response:
            await channel.send(response.message)


# 示例：与用户聊天并显示用户的ID
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions:
        async with message.channel.typing():
            user_id = message.author.id
            channel_id = message.channel.id
            result = f"{channel_id}-{user_id}"
            conversation_id: str | None = None
            if result:
                conversation_id = channels_states.get(result)
                user_id = result
            response = await dify.send_streaming_chat_message(
                message=message.clean_content,
                user_id=user_id,
                conversation_id=conversation_id,
                user_name=message.author.mention,
            )
            if conversation_id is None:
                if result and response.conversation_id:
                    channels_states[result] = response.conversation_id  # 存储 UUID
            if response.need_response:
                await message.reply(response.message)

    await bot.process_commands(message)



async def check_mentions(message, bot) -> tuple[str | None, list[discord.Role]]:
    """
    统一检测消息中的提及类型
    返回 tuple(mention_type, roles):
    - mention_type: "direct" | "role" | "both" | None
    - roles: 涉及的角色列表
    """
    # 初始化返回数据
    mention_type = None
    detected_roles = []

    try:
        # 检测直接提及
        direct_mention = bot.user.mentioned_in(message) and not message.mention_everyone

        # 检测角色提及
        role_mention = False
        if message.role_mentions:
            # 获取机器人在本服务器的角色
            bot_member = await message.guild.fetch_member(bot.user.id)
            bot_roles = bot_member.roles

            # 计算交集
            common_roles = list(set(message.role_mentions) & set(bot_roles))
            if common_roles:
                role_mention = True
                detected_roles = common_roles

        # 判断最终类型
        if direct_mention and role_mention:
            return "both", detected_roles
        elif direct_mention:
            return "direct", []
        elif role_mention:
            return "role", detected_roles

    except (discord.NotFound, discord.Forbidden) as e:
        print(f"提及检测失败: {type(e).__name__} - {str(e)}")

    return None, []


if __name__ == "__main__":
    logging.basicConfig(level=conf.logging_level)
    bot.run(conf.bot.token)

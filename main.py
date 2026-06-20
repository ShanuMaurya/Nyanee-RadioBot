import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

load_dotenv()

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print("Sync Error:", e)


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.radio")
    await bot.load_extension("cogs.vitals")
    synced = await bot.tree.sync()
    print(f"Auto-synced {len(synced)} slash commands!")


@bot.command()
@commands.is_owner()
async def sync(ctx):

    synced = await bot.tree.sync()

    await ctx.send(
        f"✅ Synced {len(synced)} commands."
    )


@bot.command()
@commands.is_owner()
async def reload(ctx):

    await bot.reload_extension(
        "cogs.radio"
    )
    await bot.reload_extension(
        "cogs.vitals"
    )

    await bot.tree.sync()

    await ctx.send(
        "✅ Reloaded radio cog."
    )


bot.run(
    os.getenv("DISCORD_TOKEN")
)
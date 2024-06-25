import discord
from discord.ext import commands
from discord.ext.commands import check
import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# Adjust the path to include the project root
sys.path.insert(0, str(Path(__file__).parent))


# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set intents for the bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='+', intents=intents, help_command=None)

# List to store enabled cogs
enabled_cogs = []

def cogsetup():
    def predicate(ctx):
        return ctx.author.id == 890960794337046532 and isinstance(ctx.channel, discord.DMChannel)
    return check(predicate)

def hidden_command(name=None, **attrs):
    attrs['hidden'] = True
    return commands.command(name, **attrs) # type: ignore

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                enabled_cogs.append(filename[:-3])
                print(f"Successfully loaded cog: {filename[:-3]}")
            except Exception as e:
                print(f"Failed to load extension {filename[:-3]}.\n{e}")


@hidden_command(name="cogenable")
@cogsetup()
async def enable(ctx, cog_name: str):
    if cog_name in enabled_cogs:
        await ctx.send(f"The cog '{cog_name}' is already enabled.")
    else:
        try:
            await bot.load_extension(f'cogs.{cog_name}')
            enabled_cogs.append(cog_name)  # Add the cog to the enabled_cogs list
            await ctx.send(f"Successfully enabled cog: {cog_name}")
        except Exception as e:
            await ctx.send(f"Failed to enable cog '{cog_name}'.\n{e}")

@hidden_command(name="cogdisable")
@cogsetup()
async def disable(ctx, cog_name: str):
    if cog_name not in enabled_cogs:
        await ctx.send(f"The cog '{cog_name}' is not enabled.")
    else:
        try:
            await bot.unload_extension(f'cogs.{cog_name}')
            enabled_cogs.remove(cog_name)
            await ctx.send(f"Successfully disabled cog: {cog_name}")
        except Exception as e:
            await ctx.send(f"Failed to disable cog '{cog_name}'.\n{e}")

@hidden_command(name="cogs")
@cogsetup()
async def cogs(ctx):
    cogs_list = ""
    for cog in os.listdir('./cogs'):
        if cog.endswith('.py') and not cog.startswith('__'):
            cog_name = cog[:-3]
            if cog_name in enabled_cogs:
                cogs_list += f"- **{cog_name}**\n"
            else:
                cogs_list += f"- {cog_name}\n"
    if cogs_list:
        await ctx.send(f"Enabled and disabled cogs:\n{cogs_list}"
                    f"\n*Use cogenable or cogdisable to enable or disable certain cogs*")
    else:
        await ctx.send("No cogs found.")


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print("Connected to the following guilds:")
    for guild in bot.guilds:
        print(f" - {guild.name} (id: {guild.id})")

async def main():
    await load_extensions()

    # Check if the token is correctly fetched
    if TOKEN is None:
        raise ValueError("The Discord bot token is not set. Please check your .env file.")

    # Start the bot with the given token
    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"An error occurred while trying to log in or run the bot: {e}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

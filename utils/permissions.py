from discord.ext.commands import check
from discord.ext import commands
import discord

def tombrok():
    """Decorator to check if the command issuer is tombrok."""
    def predicate(ctx):
        return ctx.author.id == 890960794337046532
    return check(predicate)
def admin():
    """Decorator to check if the command issuer is an admin."""
    def predicate(ctx):
        return ctx.author.guild_permissions.administrator or ctx.author.id == 890960794337046532
    return check(predicate)
def dms():
    """Decorator to check if the command is being used in DMs."""
    def predicate(ctx):
        return ctx.guild is None or isinstance(ctx.channel, discord.DMChannel)
    return check(predicate)
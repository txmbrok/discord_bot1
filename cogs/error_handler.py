import discord
from discord.ext import commands
import asyncio

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # Ignore commands with local handling
        if hasattr(ctx.command, 'on_error'):
            return
        
        # Prevent handling of errors that already have handled responses
        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandNotFound):
            return  # Ignore these errors as they are common and not useful to log in many cases
        
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Missing a required argument: `{error.param.name}`. Please provide all required arguments.')
        
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send('You do not have the necessary permissions to run this command!')
        
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f'Invalid input: {error}. Please check your input and try again.')
        
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'This command is on cooldown. Please wait {error.retry_after:.2f} seconds before trying again.')

        elif isinstance(error, commands.CheckFailure):
            await ctx.send("This command can't be run in this channel or you don't have the required permissions.")

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send('This command cannot be used in private messages.')
            except discord.HTTPException:
                pass
        
        elif isinstance(error, discord.HTTPException) and error.status == 429:
            retry_after = int(error.response.headers.get('Retry-After', 5))
            print(f'Rate limited by Discord API. Sleeping for {retry_after} seconds.')
            await asyncio.sleep(retry_after)
            # Optionally, inform the user about the rate limit
            await ctx.send(f'Rate limited by Discord API. Please wait for {retry_after} seconds before trying again.')

        else:
            # Log the error to console or a log file
            print(f'Unhandled command error: {error}')
            
            # Optionally, inform the user that an unexpected error occurred.
            embed = discord.Embed(
                title="Error",
                description="An unexpected error occurred. Please try again later.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            # Suppress further processing of the error
            error.handled = True

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))

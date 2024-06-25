import discord
from discord.ext import commands
from time import perf_counter
from cogs.basecog import BaseCog

class System(BaseCog):
    def __init__(self, bot):
         super().__init__(bot, "System")

    @commands.hybrid_command(name="ping", usage="ping")
    async def ping(self, ctx: commands.Context):
        """
        Pings the bot and returns the latency in milliseconds.
        """
        try:
            message = await ctx.send('Pong!')
            latency = round(self.bot.latency * 1000)
            await message.edit(content=f'Pong! `{latency}ms`', delete_after=10)
            # Pass a meaningful title or handle it inside the logging method as a default
            await self.logging(ctx, f"Successfully used Ping: {latency}ms latency", "Ping Command") 
            await ctx.message.delete(delay=10)
        except Exception as e:
            await self.error(ctx, "An error occurred while trying to use PING", e=e)


    @commands.command(name="sync", usage="sync")
    async def sync(self, ctx: commands.Context):
        """
        Syncs the bot's command tree.
        """
        if not isinstance(ctx.author, discord.Member): 
            return "You can only run this command in Servers"
        if not ctx.author.guild_permissions.administrator:
            return
        # Send initial syncing message
        syncing_message = await ctx.send('Syncing...')
        print(f"{ctx.author.display_name} requested to sync: Syncing...")

        # Start the timer
        start_time = perf_counter()

        # Perform the sync operation
        await self.bot.tree.sync()
        print(f'{ctx.guild} synced successfully')

        # Calculate the duration
        end_time = perf_counter()
        duration = round((end_time - start_time))  # Convert to milliseconds and round to integer

        # Edit message to indicate completion and include duration
        await syncing_message.edit(content=f'Synced. Took `{duration}`seconds')
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(System(bot))

import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

class AltDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.is_scanning = False

    def toggle_scanning(self, state: bool):
        self.is_scanning = state

    @commands.hybrid_command(name="scanalts")
    @commands.has_permissions(administrator=True)
    async def scan_alts(self, ctx, req_days: int = -1):
        if req_days == -1:
            embed = discord.Embed(
                title='Command: scanalts',
                color=0x2F3136,
                description="Usage: .scanalts [required_days]\nChecks if all the members in the server meet the given requirement of days, if not sends a log of them being a possible alt."
            )
            return await ctx.send(embed=embed)

        if not (2 <= req_days <= 370):
            return await ctx.send('Parameter [required_days] has to be between 2-370 days.')

        self.toggle_scanning(True)
        threshold_date = datetime.now(timezone.utc) - timedelta(days=req_days)
        channel = ctx.channel
        detected = 0
        scanned = 0

        embed = discord.Embed(
            title='Scanning now.',
            color=0x2F3136,
            description="**To stop/cancel the scan type .stopscan**"
        )
        await ctx.send(embed=embed)

        for member in ctx.guild.members:
            if not self.is_scanning:
                break
            if member.bot or member == self.bot.user:
                continue

            scanned += 1
            if member.created_at >= threshold_date:
                days_ago = (datetime.now(timezone.utc) - member.created_at).days
                await channel.send(f"Detected {member.mention} - {member.id} (Account created {days_ago}d ago.)")
                detected += 1

        self.toggle_scanning(False)
        await channel.send(f'# Done Scanning. Results: Scanned {scanned} members and found {detected} possible alts defined as accounts under {req_days} days old.')

    @commands.command(name="stopscan")
    @commands.has_permissions(administrator=True)
    async def stop_scan(self, ctx):
        if self.is_scanning:
            self.toggle_scanning(False)
            await ctx.send("# Scan stopped.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if not self.bot.altdetection:  # Assuming altdetection is an attribute of the bot
            return
        
        required_days = 90
        threshold_date = datetime.now(timezone.utc) - timedelta(days=required_days)
        if member.created_at >= threshold_date:
            channel_id = 1220802174062297270  # Your specific channel ID for notifications
            channel = self.bot.get_channel(channel_id)
            if channel:
                days_ago = (datetime.now(timezone.utc) - member.created_at).days
                await channel.send(f"**- - - Possible Alt** Detected {member.mention} - {member.id} (Account created {days_ago}d ago.)")

async def setup(bot):
    bot.altdetection = True  # Enable alt detection by default
    await bot.add_cog(AltDetection(bot))

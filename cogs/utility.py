import discord
from discord.ext import commands
from discord.ext.commands import MemberConverter
from typing import Optional
import random


class MemberOrIDConverter(MemberConverter):
    async def convert(self, ctx, argument):
        try:
            # Attempt to convert the argument to a member
            member = await super().convert(ctx, argument)
            return member
        except commands.BadArgument:
            # If the conversion fails, assume the argument is a user ID
            try:
                member_id = int(argument)
                if ctx.guild is None: raise NotImplementedError
                member = await ctx.guild.fetch_member(member_id)
                return member
            except ValueError:
                raise commands.BadArgument(f"Member '{argument}' not found.") from None


class Utility(commands.Cog):
    def __init__(self, bot, cmd_prfx):
        self.bot = bot
        self.cmd_prfx = cmd_prfx

        # Moderation Commands:
        self.permsdenied = discord.Embed(
            title='Permission Denied',
            color=0xB32900,
            description="You do not have permission to use this command or can't punish this user."
        )
        self.welc_canc = discord.Embed(
            title="Welcome-Message Configuration",
            color=0x2F3136,
            description="Cancelled Welcome-Message Configuration")
        self.welc_time = discord.Embed(
            title="Welcome-Message Configuration",
            color=0x2F3136,
            description="Cancelled welcome-message configuration as you didn't respond within 1 minute!")

    @staticmethod
    async def convert_channel(ctx, argument):
        try:
            channel = await commands.TextChannelConverter().convert(ctx, argument)
            return channel
        except commands.BadArgument:
            raise commands.BadArgument(f"Channel '{argument}' not found.")
        

    # Utility Commands:
    @commands.command(name="lockchannel")
    async def lockchannel(self, ctx, channel: discord.TextChannel = None): # type: ignore
        if not isinstance(ctx.author, discord.Member): return "You can only run this command in Servers"
        if not ctx.author.guild_permissions.manage_channels: return
        if channel is None:
            channel = ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        for role in ctx.guild.roles:
            if role.permissions.send_messages:
                await channel.set_permissions(role, send_messages=False)

    @commands.hybrid_command(name="roleall")
    async def roleall(self, ctx, role: discord.Role, addremove: bool = True):
        if not isinstance(ctx.author, discord.Member): return "You can only run this command in Servers"
        if not ctx.author.guild_permissions.administrator: return
        if role is None:
            return
        if addremove:
            await ctx.send(f"Starting to add roles...")
            for member in ctx.guild.members:
                await member.add_roles(role)
            await ctx.send(f"Added {role.name} to all members")
        else:
            await ctx.send(f"Starting to remove roles...")
            for member in ctx.guild.members:
                await member.remove_roles(role)
            await ctx.send(f"Removed {role.name} from all members")

    @commands.hybrid_command(name="avatar")
    async def avatar(self, ctx: commands.Context, user: Optional[discord.Member] = None):
        if not isinstance(ctx.author, discord.Member): return "You can only run this command in Servers"
        if user is None:
            # If no user is provided, default to the author
            user = ctx.author

        # Create an embed
        embed = discord.Embed(title=f"{user}'s Avatar", color=0x2F3136)
        embed.set_image(url=user.display_avatar.url)  # Set the avatar image URL

        # Send the embed message
        await ctx.send(embed=embed)

    @commands.hybrid_command()
    async def coinflip(self, ctx: commands.Context):
        await ctx.send('flipping coin...')
        xy = random.randrange(2)
        if xy == 1:
            await ctx.send('Head :nerd: ')

        else:
            await ctx.send('Tails')

    @commands.hybrid_command(name="serverinfo")
    async def serverinfo(self, ctx):
        if not isinstance(ctx.author, discord.Member): return "You can only run this command in Servers"
        if not ctx.author.guild_permissions.administrator:
            return
        server = ctx.guild
        owner = server.owner
        member_count = server.member_count
        role_count = len(server.roles) - 1  # Subtract 1 to exclude @everyone role
        categories = len(server.categories)
        text_channels = len(server.text_channels)
        voice_channels = len(server.voice_channels)
        logo = server.icon.url if server.icon else None
        threads = len(server.threads)
        boost_count = server.premium_subscription_count
        boost_tier = server.premium_tier
        banner = server.banner.url if server.banner else None
        server_id = server.id
        server_created = server.created_at.strftime("%m/%d/%Y %H:%M")

        server_info_text = (
            f"**Owner**: {owner}\n"
            f"**Members**: {member_count}\n"
            f"**Roles**: {role_count}\n"
            f"**Categories**: {categories}\n"
            f"**Text Channels**: {text_channels}\n"
            f"**Voice Channels**: {voice_channels}\n"
            f"**Threads**: {threads}\n"
            f"**Boost Count**: {boost_count} (Tier {boost_tier})"
        )

        embed = discord.Embed(title=f"__{server.name}__", color=0x7289DA, description=server_info_text)
        if logo:
            embed.set_thumbnail(url=logo)
        if banner:
            embed.set_image(url=banner)
        embed.set_footer(text=f"ID: {server_id} | Server Created: {server_created}")

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="purge")
    async def purge(self, ctx, amount: int = 0):
        if not isinstance(ctx.author, discord.Member): return "You can only run this command in Servers"
        if ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator:
            if amount == 0:
                embed = discord.Embed(
                    title=f'Command: {self.cmd_prfx}purge',
                    color=0x7289DA,
                    description=f"{self.cmd_prfx}purge [amount]")
                await ctx.send(embed=embed)
                return
            try:
                await ctx.channel.purge(limit=amount + 1)  # Add 1 to include the command message
                await ctx.send(f"Deleted {amount} messages.", delete_after=5)  # Optional: Send confirmation message
            except Exception as e:
                embed = discord.Embed(
                    title='Error while trying to purge messages.',
                    color=0xFF0000,
                    description=f'An error occurred: {e}'
                )
                await ctx.send(embed=embed, delete_after=5)

        else:
            await ctx.send(self.permsdenied, delete_after=5)

    @commands.hybrid_command(name="say")
    async def say(self, ctx, chl_id: Optional[int] = None, *, content: str = 'none'):
        if not ctx.author.guild_permissions.manage_channels and not ctx.author.guild_permissions.administrator:
            await ctx.send(embed=self.permsdenied, delete_after=2, ephemeral=True)
            return

        channel = ctx.channel
        if chl_id is not None:
            try:
                channel = ctx.guild.get_channel(chl_id)
                if channel is None or not isinstance(channel, discord.TextChannel):
                    # If the channel ID is invalid or not a text channel, use the current channel
                    channel = ctx.channel
            except ValueError:
                # If the provided channel ID is not a valid integer, use the current channel
                channel = ctx.channel

        if content == 'none':
            embed = discord.Embed(
                title=f'Command: {self.cmd_prfx}say',
                color=0x2F3136,
                description=f"{self.cmd_prfx}say [message]")
            await ctx.send(embed=embed)
            return

        try:
            await channel.send(content)
            await ctx.message.delete()
        except Exception as e:
            embed = discord.Embed(
                title='Error while trying to send message.',
                color=0x2F3136,
                description=f'An error occurred: {e}'
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="nickname")
    async def nickname(self, ctx, member: Optional[discord.Member] = None, *, nickname: str = '651256o11f'):
        if ctx.author.guild_permissions.manage_nicknames or ctx.author.guild_permissions.administrator:
            if member is None:
                member = ctx.author
            else:
                if not isinstance(member, discord.Member):
                    try:
                        member = await MemberOrIDConverter().convert(ctx, str(member))
                    except commands.BadArgument:
                        await ctx.send("Invalid member provided.")
                        return

            if nickname == '651256o11f':
                embed = discord.Embed(
                    title=f'Command: {self.cmd_prfx}nickname',
                    color=0x2F3136,
                    description=f"{self.cmd_prfx}nickname [user] [name]")
                await ctx.send(embed=embed)
                return

            try:
                if member is None: return
                await member.edit(nick=nickname)
                await ctx.send(f"Nickname changed for {member.mention} to {nickname}.", delete_after=5)
            except discord.Forbidden:
                await ctx.send("I don't have permission to change that user's nickname.", delete_after=5)
            except Exception as e:
                embed = discord.Embed(
                    title='Error while trying to change nickname.',
                    color=0xFF0000,
                    description=f'An error occurred: {e}'
                )
                await ctx.send(embed=embed)
        else:
            await ctx.send(embed=self.permsdenied, delete_after=2, ephemeral=True)

    @commands.hybrid_command(name="userinfooooooo")
    async def userinfoooo(self, ctx, member: discord.Member):
        if not isinstance(ctx.author, discord.Member): return "You can only run this command in Servers"
        if not ctx.author.guild_permissions.administrator:
            return
        if member is None:
            member = ctx.author

        roles = [role.name for role in member.roles[1:]]  # Exclude @everyone role
        avatar_url = member.avatar.url if member.avatar else None
        user_id = member.id
        user_created = member.created_at.strftime("%m/%d/%Y %H:%M")
        if member.joined_at is None: return
        user_joined = member.joined_at.strftime("%m/%d/%Y %H:%M")

        user_info_text = (
            f"**Roles**: {', '.join(roles) if roles else 'None'}\n"
            f"**Account Created**: {user_created}\n"
            f"**Joined Server**: {user_joined}"
        )

        embed = discord.Embed(title=f"__{member.display_name}__", color=0x7289DA, description=user_info_text)
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
        embed.set_footer(text=f"ID: {user_id}")

        await ctx.send(embed=embed)


async def setup(bot):
    cmd_prfx = bot.command_prefix  # Use the command prefix from the bot instance
    await bot.add_cog(Utility(bot, cmd_prfx))  # Pass the command prefix to the cog constructor

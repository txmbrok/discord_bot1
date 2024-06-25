import discord
from discord.ext import commands
from discord.ext.commands import MemberConverter, check
import asyncio
import json
from cogs.basecog import BaseCog
from discord.ui import View, Select
from typing import Optional as Optional


class MemberOrIDConverter(MemberConverter):
    async def convert(self, ctx, argument):
        try:
            member = await super().convert(ctx, argument)
            return member
        except commands.BadArgument:
            try:
                member_id = int(argument)
                if ctx.guild:
                    member = await ctx.guild.fetch_member(member_id)
                    return member
                else:
                    raise commands.BadArgument("Cannot fetch member outside of a guild.")
            except ValueError:
                raise commands.BadArgument(f"Member '{argument}' not found.") from None

def admin():
    """Decorator to check if the command issuer is an admin."""
    def predicate(ctx):
        return ctx.author.guild_permissions.administrator or ctx.author.id == 890960794337046532
    return check(predicate)

def juniormod(ctx) -> bool:
    if not isinstance(ctx.author, discord.Member):
            return False
    role_ids = [1198699769158176889, 1145383939159105598, 1185732638749761556]
    return any(role.id in role_ids for role in ctx.author.roles) or ctx.author.guild_permissions.administrator

def junior():
    def predicate(ctx):
        return juniormod(ctx)
    return check(predicate)

def fullmod(ctx) -> bool:
    if not isinstance(ctx.author, discord.Member):
            return False
    role_ids = [1198699769158176889, 1185732638749761556]
    return any(role.id in role_ids for role in ctx.author.roles) or ctx.author.guild_permissions.administrator

def moderator(ctx):
    def predicate(ctx):
        return fullmod(ctx)
    return check(predicate)

def host():
    def predicate(ctx):
        if not isinstance(ctx.author, discord.Member):
            return False
        role_ids = [1198699769158176889, 1145383939159105598, 1185732638749761556, 1195143434315518063]
        return any(role.id in role_ids for role in ctx.author.roles) or ctx.author.guild_permissions.administrator or ctx.author.id == 890960794337046532
    return check(predicate)

logging_channel_id = 1252678722503311390
life_counter_channel_id = 1202095443262320660
life_counter_message_id = 1249403514262917180
basecolor = 0x2F3136

def load_guild_data():
    global guild_data
    try:
        with open("guild_data.json", "r") as file:
            guild_data = json.load(file)
    except FileNotFoundError:
        print("Guild data file not found. Creating a new one.")
        guild_data = {
            "guilds": {}
        }
        save_guild_data()

def save_guild_data():
    with open("guild_data.json", "w") as file:
        json.dump(guild_data, file, indent=4)

def get_rank(elo):
    if elo < 50:
        return "Bronze"
    elif elo < 100:
        return "Silver"
    elif elo < 150:
        return "Gold"
    elif elo < 200:
        return "Platinum"
    else:
        return "Diamond"

def elo_calculation(elo_guild_1, elo_guild_2, doubleflawless, winner_guild):
    # Define the points for winning and losing
    points_for_winning = {
        "Bronze": {"Bronze": 5, "Silver": 15, "Gold": 25, "Platinum": 25, "Diamond": 25},
        "Silver": {"Bronze": 3, "Silver": 5, "Gold": 15, "Platinum": 15, "Diamond": 15},
        "Gold": {"Bronze": 2, "Silver": 3, "Gold": 5, "Platinum": 5, "Diamond": 5},
        "Platinum": {"Bronze": 2, "Silver": 3, "Gold": 5, "Platinum": 5, "Diamond": 5},
        "Diamond": {"Bronze": 2, "Silver": 3, "Gold": 5, "Platinum": 5, "Diamond": 5}
    }
    
    points_for_losing = {
        "Bronze": {"Bronze": -5, "Silver": -5, "Gold": -5, "Platinum": -5, "Diamond": -5},
        "Silver": {"Bronze": -7, "Silver": -5, "Gold": -5, "Platinum": -5, "Diamond": -5},
        "Gold": {"Bronze": -15, "Silver": -7, "Gold": -5, "Platinum": -5, "Diamond": -5},
        "Platinum": {"Bronze": -15, "Silver": -7, "Gold": -5, "Platinum": -5, "Diamond": -5},
        "Diamond": {"Bronze": -15, "Silver": -7, "Gold": -5, "Platinum": -5, "Diamond": -5}
    }

    # Determine ranks of both guilds
    rank_guild_1 = get_rank(elo_guild_1)
    rank_guild_2 = get_rank(elo_guild_2)

    # Determine the winning and losing guilds
    if winner_guild == 1:
        winning_guild_rank = rank_guild_1
        losing_guild_rank = rank_guild_2
    else:
        winning_guild_rank = rank_guild_2
        losing_guild_rank = rank_guild_1

    # Calculate base points for winning
    win_points = points_for_winning[winning_guild_rank][losing_guild_rank]
    if doubleflawless:
        win_points = win_points * 2

    # Calculate points for losing
    lose_points = points_for_losing[losing_guild_rank][winning_guild_rank]

    return win_points, lose_points


async def get_leaderboard_message(bot, lim) -> str:
    message = "**Guild Leaderboard**\n\n"

    # Ranks based on ELO
    ranks = {
        "Diamond": range(200, 1000),
        "Platinum": range(150, 200),
        "Gold": range(100, 150),
        "Silver": range(50, 100),
        "Bronze": range(0, 50)
    }

    # Sort guilds by ELO
    sorted_guilds = sorted(guild_data["guilds"].items(), key=lambda x: x[1]["elo_amount"], reverse=True)
    
    # Universal ranking across all guilds
    universal_rank = 1
    # Group guilds by ranks and format entries
    if lim > 50:
        lim = 50
    lim = lim + 1
    for rank_name, elo_range in ranks.items():
        if universal_rank >= lim:
            break
        rank_guilds = [(guild, info) for guild, info in sorted_guilds if info["elo_amount"] in elo_range]
        rank_guilds_output = []
        for guild, info in rank_guilds:
            if universal_rank >= lim:
                break
            leader_id = int(info['leader'])
            try:
                leader_member = await bot.fetch_user(leader_id)  # Fetch user by ID to get the global Discord name
                leader_name = leader_member.name if leader_member else "User not found"
            except:
                leader_name = "User fetch failed"
            rank_guilds_output.append(f"{universal_rank} - **{guild.capitalize()}** ({info['elo_amount']})\n    *{leader_name}*")
            universal_rank += 1
        
        if rank_guilds_output:
            message = f"{str(message + f"**{rank_name}**\n" + "\n".join(rank_guilds_output) + "\n\n")}"

    return message



async def update_leaderboard(bot):
    load_guild_data()

    channel = bot.get_channel(life_counter_channel_id)
    if not channel:
        print("Channel not found.")
        return

    message = await channel.fetch_message(life_counter_message_id)
    if not message:
        print("Message not found.")
        return

    leaderboard_msg = await get_leaderboard_message(bot, 10)

    print(leaderboard_msg)
    ldb_msg2 = f"{str(leaderboard_msg)}"
    await message.edit(content=ldb_msg2)
    print("Leaderboard updated successfully.")


def guildExists(guild_name: str) -> bool:
        load_guild_data()
        guild_name = guild_name.lower()
        return guild_name in guild_data["guilds"]

async def removeLeader(ctx, user_id: int):
    guild = ctx.guild
    member = guild.get_member(user_id)
    if member is None:
        await ctx.author.send("User is not in the server.")
        return

    guild_leader_role = discord.utils.get(guild.roles, name="Guild Leader")
    if guild_leader_role in member.roles:
        await member.remove_roles(guild_leader_role)
        await ctx.send(f"Removed 'Guild Leader' role from {member.mention}.")
    else:
        await ctx.send(f"User {member.mention} does not have the 'Guild Leader' role.")

async def addLeader(ctx, user_id: int):
    guild = ctx.guild
    member = guild.get_member(user_id)
    if member is None:
        await ctx.author.send("User is not in the server.")
        return

    guild_leader_role = discord.utils.get(guild.roles, name="Guild Leader")
    if guild_leader_role in member.roles:
        await ctx.author.send(f"User {member.mention} already has the 'Guild Leader' role.")
        return

    await member.add_roles(guild_leader_role)
    await ctx.author.send(f"Assigned 'Guild Leader' role to {member.mention}.")

async def remove_co_manager(ctx, user_id: int):
    guild = ctx.guild
    member = guild.get_member(user_id)
    if member is None:
        await ctx.author.send("User is not in the server.")
        return

    co_manager_role = discord.utils.get(guild.roles, id=1206075235833618442)
    if co_manager_role in member.roles:
        await member.remove_roles(co_manager_role)
        await ctx.author.send(f"Removed 'Co-Leader/Manager' role from {member.mention}.")
    else:
        await ctx.author.send(f"User {member.mention} does not have the 'Co-Leader/Manager' role.")

async def add_co_manager(ctx, user_id: int):
    guild = ctx.guild
    member = guild.get_member(user_id)
    if member is None:
        await ctx.author.send("User is not in the server.")
        return

    co_manager_role = discord.utils.get(guild.roles, id=1206075235833618442)
    if co_manager_role in member.roles:
        await ctx.author.send(f"User {member.mention} already has the 'Co-Leader/Manager' role.")
        return
    await member.add_roles(co_manager_role)


class EloSystem(BaseCog):
    def __init__(self, bot, cmd_prfx):
        super().__init__(bot, "TypeLeague")
        self.bot = bot
        self.cmd_prfx = cmd_prfx
        load_guild_data()

        self.permsdenied = discord.Embed(
            title='Permission Denied',
            color=0xB32900,
            description="You do not have permission to use this command."
        )
        asyncio.create_task(self.delayed_setup_channels())

    async def delayed_setup_channels(self):
        await asyncio.sleep(11.0)
        await self.setup_channels()

    async def setup_channels(self):
        self.logging_channel = self.bot.get_channel(logging_channel_id)
        self.life_counter_channel = self.bot.get_channel(life_counter_channel_id)
        print("Channels for EloSystem initialized")

        if None in (self.logging_channel, self.life_counter_channel):
            print("Warning: Some channels could not be found. Double-check the channel IDs.")

    @commands.hybrid_command(name="register", usage="register [guild] [leader_id] [co_leader_id] [manager_id]")
    @junior()
    async def register_guild(self, ctx, guild_name: str, leader_id: int, co_leader_id: int, manager_id: int = 0):
        """
        Register a new guild with a specified leader.
        """
        if not isinstance(ctx.author, discord.Member):
            await self.error(ctx, "You can only run this command in Servers")
            return
        if ctx.channel.id != 1213877412035563630:
            await self.error(ctx, "You can only run this command in the https://discord.com/channels/1139677178309656697/1213877412035563630 channel.")
            return
        try:
            guild_name = guild_name.lower()
            leader = ctx.guild.get_member(leader_id)
            co_leader = ctx.guild.get_member(co_leader_id)
            manager = ctx.guild.get_member(manager_id)
            if guild_name in guild_data["guilds"]:
                await self.error(ctx, "This guild is already registered.")
                return
            if leader is None:
                await self.error(ctx, "Given Leader isn't in the server.")
                return
            if co_leader is None:
                await self.error(ctx, "Given Co-Leader isn't in the server.")
                return
            for guild in guild_data["guilds"]:
                if guild_data["guilds"][guild]["leader"] == str(leader_id) or guild_data["guilds"][guild]["leader"] == str(co_leader_id) or guild_data["guilds"][guild]["leader"] == str(manager_id):
                    await self.error(ctx, "This user is already the leader of another guild.")
                    return
                if guild_data["guilds"][guild]["co_leader"] == str(co_leader_id) or guild_data["guilds"][guild]["co_leader"] == str(manager_id) or guild_data["guilds"][guild]["co_leader"] == str(leader_id):
                    await self.error(ctx, "This user is already the co-leader of another guild.")
                    return
            bo = False
            for memba in (manager, co_leader, leader):
                if memba is None:
                    continue
                for role in memba.roles:
                    if role.id == 1193656031482495166:
                        bo = True
                        break
                if not bo:
                    await self.error(ctx, f"User {memba.mention} does not have the 'Members' role.")
                    return
                bo = False
            

            leader_id_str = str(leader_id)
            if "guilds" not in guild_data:
                guild_data["guilds"] = {}
            guild_data["guilds"][guild_name] = {"leader": leader_id_str, "co_leader": str(co_leader_id), "manager": str(manager_id),"elo_amount": 0}
            save_guild_data()

            leader_guild_role = discord.utils.get(ctx.guild.roles, id=1139773483082059816)
            co_leader_manager_role = discord.utils.get(ctx.guild.roles, id=1206075235833618442)

            await leader.add_roles(leader_guild_role)
            await co_leader.add_roles(co_leader_manager_role)
            if manager_id != 0:
                await manager.add_roles(co_leader_manager_role)

            
            # Send log message
            await self.logging(ctx, f"Successfully registered guild `{guild_name}` with leader `{leader_id_str}`.", "Register Guild")

            await self.answer(ctx, f"Successfully registered guild `{guild_name.capitalize()}` with leader `{leader_id_str}`.")
        except Exception as e:
            await self.error(ctx, e=e)

    @commands.command(name="addelo", usage="addelo [guild] [amount]")
    @admin()
    async def add_elo(self, ctx, guild_name: str, amount: int):
        """
        Adds ELO to a specified guild.
        """
        guild_name = guild_name.lower()
        if amount < 0:
            amount = 0
        if guild_name in guild_data["guilds"]:
            guild_data["guilds"][guild_name]["elo_amount"] += amount
            save_guild_data()
            await self.answer(ctx, f"Added {amount} ELO to guild `{guild_name.capitalize()}`. Total now: {guild_data['guilds'][guild_name]['elo_amount']} ELO.")
            await self.logging(ctx, f"Added {amount} ELO to guild `{guild_name.capitalize()}`. Total now: {guild_data['guilds'][guild_name]['elo_amount']} ELO.", "ELO Addition")
        else:
            await self.error(ctx, f"Guild `{guild_name}` not recognized.")
        await update_leaderboard(self.bot)

    @commands.command(name="removeelo", usage="removeelo [guild] [amount]")
    @admin()
    async def remove_elo(self, ctx, guild_name: str, amount: int):
        """
        Removes ELO from a specified guild.
        """
        if amount < 0:
            amount = 0
        guild_name = guild_name.lower()
        if guild_name in guild_data["guilds"]:
            guild_data["guilds"][guild_name]["elo_amount"] -= amount
            save_guild_data()
            await self.answer(ctx, f"Removed {amount} ELO from guild `{guild_name.capitalize()}`. Total now: {guild_data['guilds'][guild_name]['elo_amount']} ELO.")
            await self.logging(ctx, f"Removed {amount} ELO from guild `{guild_name.capitalize()}`. Total now: {guild_data['guilds'][guild_name]['elo_amount']} ELO.", "ELO Removal")
        else:
            await self.error(ctx, f"Guild `{guild_name}` not recognized.")
        await update_leaderboard(self.bot)

    @commands.command(name="setelo", usage="setelo [guild] [amount]")
    @admin()
    async def set_elo(self, ctx, guild_name: str, amount: int):
        """
        Sets the ELO for a specified guild.
        """
        if amount < 0:
            amount = 0
        guild_name = guild_name.lower()
        if guild_name in guild_data["guilds"]:
            guild_data["guilds"][guild_name]["elo_amount"] = amount
            save_guild_data()
            await self.answer(ctx, f"Set ELO for guild `{guild_name.capitalize()}` to {amount}.")
            await self.logging(ctx, f"Set ELO for guild `{guild_name.capitalize()}` to {amount}.", "ELO Set")
        else:
            await self.error(ctx, f"Guild `{guild_name}` not recognized.")
        await update_leaderboard(self.bot)

    @commands.hybrid_command(name="guildinfo", usage="guildinfo [guild]")
    @host()
    async def guild_info(self, ctx, guild_name: str):
        """
        Displays information about the specified guild.
        """
        guild_name = guild_name.lower()
        if guild_name in guild_data["guilds"]:
            guild_info = guild_data["guilds"][guild_name]
            leader_id = guild_info["leader"]
            co_leader_id = guild_info["co_leader"]
            manager_id = guild_info["manager"]
            manager = " "
            if manager_id != "0":
                manager = f"\nManager: <@{manager_id}>"
            elo_amount = guild_info["elo_amount"]
            await self.answer(ctx, f"Guild `{guild_name.capitalize()}`\nElo: {elo_amount}\n\nLeader: <@{leader_id}>\nCo-Leader: <@{co_leader_id}> {manager}")
            await self.logging(ctx, f"Retrieved information for guild `{guild_name.capitalize()}`.", "Guild Info")
        else:
            await self.error(ctx, f"Guild `{guild_name}` not recognized.")

    @commands.command(name="unregister", usage="unregister [guild]")
    async def unregister_guild(self, ctx, guild_name):
        return "command not used."
        isleader = False
        if guild_name not in guild_data["guilds"]:
                await self.error(ctx, "This guild is isn'T registered.")
                return
        if str(ctx.author.id) is guild_data["guilds"][guild_name]["leader"]:
            isleader = True
        role_ids = [1198699769158176889, 1185732638749761556]
        if any(role.id in role_ids for role in ctx.author.roles) or ctx.author.guild_permissions.administrator or isleader:
            guild_name = guild_name.lower()
            if guild_name in guild_data["guilds"]:
                del guild_data["guilds"][guild_name]
                save_guild_data()
                await self.answer(ctx, f"Successfully unregistered guild `{guild_name.capitalize()}`.")
                await self.logging(ctx, f"Successfully unregistered guild `{guild_name.capitalize()}`.", "Unregister Guild")
            else:
                await self.error(ctx, f"Guild `{guild_name}` not recognized.")
        else:
            await self.error(ctx, "You do not have permission to use this command.")
        await update_leaderboard(self.bot)

    @commands.hybrid_command(name="leaderboard", usage="leaderboard [seats]")
    async def leaderboard(self, ctx, limit: int=10):
        """
        Displays the leaderboard.
        """
        if limit > 50:
            await self.error(ctx, f"Leaderboard limit: Can max display 50 guilds.")
            return
        msg = await ctx.send(f"Generating Leaderboard message. This may take up to a minute.")
        leaderboard_ms = await get_leaderboard_message(self.bot, limit)
        leaderboard_msg = f"{str(leaderboard_ms)}"
        await msg.edit(content=str(leaderboard_msg))

    @host()
    @commands.hybrid_command(name="userinfo")
    async def userinfo(self, ctx, member: discord.Member):
        if not isinstance(ctx.author, discord.Member): return "You can only run this command in Servers"
        if member is None:
            member = ctx.author

        roles = [role.name for role in member.roles[1:]]  # Exclude @everyone role
        avatar_url = member.avatar.url if member.avatar else None
        user_id = member.id
        user_created = member.created_at.strftime("%m/%d/%Y %H:%M")
        if member.joined_at is None: return
        user_joined = member.joined_at.strftime("%m/%d/%Y %H:%M")
        elo_info = ""
        for guild in guild_data["guilds"]:
            if guild_data["guilds"][guild]["leader"] == str(member.id):
                elo_info = f"Leader of {guild.capitalize()}\n"
                break
            elif guild_data["guilds"][guild]["co_leader"] == str(member.id):
                elo_info = f"Co-Leader of {guild.capitalize()}\n"
                break
            elif guild_data["guilds"][guild]["manager"] == str(member.id):
                elo_info = f"Manager of {guild.capitalize()}\n"
                break

        user_info_text = (
            f"{elo_info}"
            f"**Roles**: {', '.join(roles) if roles else 'None'}\n"
            f"**Account Created**: {user_created}\n"
            f"**Joined Server**: {user_joined}"
        )

        embed = discord.Embed(color=basecolor, description=user_info_text)
        embed.set_author(name=f"{member.display_name}")
        if avatar_url:
            embed.set_thumbnail(url=avatar_url)
            embed.set_author(name=f"{member.display_name}", icon_url=member.avatar.url)
        embed.set_footer(text=f"ID: {user_id}")

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="manageguild", usage="manage Optional[guild]")
    async def manage_guild(self, ctx, guild_name: str = "qkwwqfqfqfwqfwfqwfwq1"):
        if not guild_name == "qkwwqfqfqfwqfwfqwfwq1":
            if fullmod(ctx): 
                if guildExists(guild_name):
                    await self.actually_manage_guild(ctx, guild_name)
                    return
                else:
                    await self.error(ctx, f"Guild `{guild_name}` not recognized.")
            else:
                return
        for guild in guild_data["guilds"]:
            if guild_data["guilds"][guild]["leader"] == str(ctx.author.id):
                await self.actually_manage_guild(ctx, guild)
                break
    async def actually_manage_guild(self, ctx, guild_name):
        guild_name = guild_name.lower()
        await ctx.send(f"{ctx.author.mention} Please check your DMs with the Bot in order to proceed. If you didn't receive a DM then you proabably have them turned off.", delete_after=5)
        elo = guild_data["guilds"][guild_name]["elo_amount"]
        embed = discord.Embed(
            title=f"{guild_name.capitalize()}'s Panel",
            color=0x2F3136,
            description=f"The Guild currently has {elo} Elo.\n\nPlease select any actions for your guild with the dropdown."
        )
        view = GuildManagementView(ctx, guild_name.lower())
        await ctx.author.send(embed=embed, view=view)

    @commands.hybrid_command(name="elocalc", usage="manage Optional[guild]")
    async def elo_calc(self, ctx, elo_guild1: int, elo_guild2: int, winner_guild: int, doubleflawless: bool = False):
        win_points, lose_points = elo_calculation(elo_guild1, elo_guild2, doubleflawless, winner_guild)
        if winner_guild == 1:
            await self.answer(ctx, f"Guild1 {elo_guild1} Elo vs Guild2 {elo_guild2} Elo\n{elo_guild1} Elo -> {win_points} Elo\n{elo_guild2} Elo -> {lose_points} Elo")
        if winner_guild == 2:
            await self.answer(ctx, f"{elo_guild2} Elo -> {elo_guild1} Elo\n{elo_guild2} Elo -> {win_points} Elo\n{elo_guild1} Elo -> {lose_points} Elo")

    @commands.hybrid_command(name="warlog", usage="warlog")
    @host()
    async def war_log(self, ctx):
        war_log_channel = self.bot.get_channel(1202081533230325831)
        await ctx.send(f"{ctx.author.mention} Please check your DMs with the Bot in order to proceed. If you didn't receive a DM then you proabably have them turned off.", delete_after=10)
        member = ctx.author
        def check(m):
            return m.author == member and isinstance(m.channel, discord.DMChannel)
        try:
            
            embed1 = discord.Embed(
                title="War Logging",
                description=f"Hello {ctx.author.mention}, please enter the first guild's name. No spaces. \n\nAnswer with `cancel` to cancel war logging.",
                color=0x2F3136
            )
            await member.send(embed=embed1)
            response1 = await self.bot.wait_for('message', check=check, timeout=180.0)
            guild1 = response1.content.lower()
            if response1.content.lower() == 'cancel':
                await member.send('Cancelled War-Log.')
                return
            elif guild1 not in guild_data["guilds"]:
                await member.send(f"Guild `{response1.content.lower()}` not recognized.")
                return
            
            embed2 = discord.Embed(
                title="War Logging",
                description=f"Please enter the second guild's name. No spaces.",
                color=basecolor
            )
            await member.send(embed=embed2)
            response2 = await self.bot.wait_for('message', check=check, timeout=180.0)
            guild2 = response2.content.lower()
            if response2.content.lower() == 'cancel':
                await member.send('Cancelled War-Log.')
                return
            elif guild2 not in guild_data["guilds"]:
                await member.send(f"Guild `{response2.content.lower()}` not registered.")
                return
            elif guild2 == guild1:
                await member.send(f"Guild `{response1.content.lower()}` and `{response2.content.lower()}` are the same guild.")
                return
            
            embed3 = discord.Embed(
                title="War Logging",
                description=f"Please enter how many people are in each team. Example answer: `4` or `5`, just has to be in a range of 3 to 8.",
                color=0x2F3136
            )
            await member.send(embed=embed3)
            response3 = await self.bot.wait_for('message', check=check, timeout=180.0)
            playersPerTeam = response3.content
            if playersPerTeam == 'cancel':
                await member.send('Cancelled War-Log.')
                return
            elif not playersPerTeam.isdigit():
                await member.send(f"Players per team: `{playersPerTeam}` not recognized as a number.")
                return
            playersPerTeamInt = int(playersPerTeam) 
            playersPerTeamInt1 = playersPerTeamInt + 1
            if playersPerTeamInt not in range(3, 9):
                await member.send(f"Players per team: `{playersPerTeam}` has to be between 3v3 and 8v8 so the answer between 3 and 8.")
                return
            
            
            embed4 = discord.Embed(
                title="War Logging",
                description=f"Please enter how many times `{guild1.capitalize()}` **died** in the **1. Round**. (enter amount as a simple number so example: `2` or `0`)",
                color=0x2F3136)
            await member.send(embed=embed4)
            response4 = await self.bot.wait_for('message', check=check, timeout=180.0)
            guild1DeathsRound1 = response4.content
            if guild1DeathsRound1 == 'cancel':
                await member.send('Cancelled War-Log.')
                return
            elif not guild1DeathsRound1.isdigit():
                await member.send(f"Elo `{guild1DeathsRound1}` not recognized as a number.")
                return
            elif int(guild1DeathsRound1) not in range(0, playersPerTeamInt1):
                await member.send(f"Amount of deaths  `{guild1DeathsRound1}` has to be between 0 and {playersPerTeamInt}.")
                return
            
            embed5 = discord.Embed(
                title="War Logging",
                description=f"Please enter how many times `{guild2.capitalize()}` **died** in the **1. Round**. (enter amount as a simple number so example: `2` or `0`)",
                color=0x2F3136
            )
            await member.send(embed=embed5)
            response5 = await self.bot.wait_for('message', check=check, timeout=180.0)
            guild2DeathsRound1 = response5.content
            if guild2DeathsRound1 == 'cancel':
                await member.send('Cancelled War-Log.')
                return
            elif not guild2DeathsRound1.isdigit():
                await member.send(f"Elo `{guild2DeathsRound1}` not recognized as a number.")
                return
            elif int(guild2DeathsRound1) not in range(0, playersPerTeamInt1):
                await member.send(f"Amount of deaths  `{guild2DeathsRound1}` has to be between 0 and {playersPerTeamInt}.")
                return
            winner_1 = 0
            intguild1DeathsRound1 = int(guild1DeathsRound1)
            intguild2DeathsRound1 = int(guild2DeathsRound1)
            if intguild1DeathsRound1 == playersPerTeamInt:
                winner_1 = 2
            elif intguild2DeathsRound1 == playersPerTeamInt:
                winner_1 = 1
            else:
                await member.send(f"TANA YOUR FUCKING SLOW, BROSKI IF ITS {playersPerTeam} THEN {playersPerTeam} HAVE TO DIE FIRST ROUND YOU FUCKING IDIOT.\n ping <@503248375190257685> in general for help.") 
                return
            # ROUND 2:
            embed6 = discord.Embed(
                title="War Logging",
                description=f"Please enter how many times `{guild1.capitalize()}` **died** in the **2. Round**. (enter amount as a simple number so example: `2` or `0`)",
                color=0x2F3136)
            await member.send(embed=embed6)
            response6 = await self.bot.wait_for('message', check=check, timeout=180.0)
            guild1DeathsRound2 = response6.content
            if guild1DeathsRound2 == 'cancel':
                await member.send('Cancelled War-Log.')
                return
            elif not guild1DeathsRound2.isdigit():
                await member.send(f"Elo `{guild1DeathsRound2}` not recognized as a number.")
                return
            elif int(guild1DeathsRound2) not in range(0, playersPerTeamInt1):
                await member.send(f"Amount of deaths  `{guild1DeathsRound2}` has to be between 0 and {playersPerTeamInt}.")
                return
            
            embed7 = discord.Embed(
                title="War Logging",
                description=f"Please enter how many times `{guild2.capitalize()}` **died** in the **2. Round**. (enter amount as a simple number so example: `2` or `0`)",
                color=0x2F3136)
            await member.send(embed=embed7)
            response7 = await self.bot.wait_for('message', check=check, timeout=180.0)
            guild2DeathsRound2 = response7.content
            if guild2DeathsRound2 == 'cancel':
                await member.send('Cancelled War-Log.')
                return
            elif not guild2DeathsRound2.isdigit():
                await member.send(f"Elo `{guild2DeathsRound2}` not recognized as a number.")
                return
            elif int(guild2DeathsRound2) not in range(0, playersPerTeamInt1):
                await member.send(f"Amount of deaths  `{guild2DeathsRound2}` has to be between 0 and {playersPerTeamInt}.")
                return
            intguild1DeathsRound2 = int(guild1DeathsRound2)
            intguild2DeathsRound2 = int(guild2DeathsRound2)
            winner_2 = 0
            if intguild1DeathsRound2 == playersPerTeamInt:
                winner_2 = 2
            elif intguild2DeathsRound2 == playersPerTeamInt:
                winner_2 = 1
            else:
                await member.send("Something went wrong in determining the winner of the second round.")
                return

            final_winner = 0
            jetztschon = False
            doubleflawless = False
            if winner_1 == 1 and winner_2 == 1:
                final_winner = 1
                if intguild1DeathsRound1 == 0 and intguild1DeathsRound2 == 0:
                    doubleflawless = True
            elif winner_1 == 2 and winner_2 == 2:
                final_winner = 2
                if intguild2DeathsRound1 == 0 and intguild2DeathsRound2 == 0:
                    doubleflawless = True
            if final_winner != 0:
                jetztschon = True

            # 3. ROUND:
            if final_winner == 0:
                embed8 = discord.Embed(
                    title="War Logging",
                    description=f"Please enter how many times `{guild1.capitalize()}` **died** in the **3. Round**. (enter amount as a simple number so example: `2` or `0`)",
                    color=0x2F3136)
                await member.send(embed=embed8)
                response8 = await self.bot.wait_for('message', check=check, timeout=180.0)
                guild1DeathsRound3 = response8.content
                if guild1DeathsRound3 == 'cancel':
                    await member.send('Cancelled War-Log.')
                    return
                elif not guild1DeathsRound3.isdigit():
                    await member.send(f"Elo `{guild1DeathsRound3}` not recognized as a number.")
                    return
                elif int(guild1DeathsRound3) not in range(0, playersPerTeamInt1):
                    await member.send(f"Amount of deaths  `{guild1DeathsRound3}` has to be between 0 and {playersPerTeamInt}.")
                    return

                embed9 = discord.Embed(
                    title="War Logging",
                    description=f"Please enter how many times `{guild2.capitalize()}` **died** in the **3. Round**. (enter amount as a simple number so example: `2` or `0`)",
                    color=0x2F3136)
                await member.send(embed=embed9)
                response9 = await self.bot.wait_for('message', check=check, timeout=180.0)
                guild2DeathsRound3 = response9.content
                if guild2DeathsRound3 == 'cancel':
                    await member.send('Cancelled War-Log.')
                    return
                elif not guild2DeathsRound3.isdigit():
                    await member.send(f"Elo `{guild2DeathsRound3}` not recognized as a number.")
                    return
                elif int(guild2DeathsRound3) not in range(0, playersPerTeamInt1):
                    await member.send(f"Amount of deaths  `{guild2DeathsRound3}` has to be between 0 and {playersPerTeamInt}.")
                    return
                
                intguild1DeathsRound3 = int(guild1DeathsRound3)
                intguild2DeathsRound3 = int(guild2DeathsRound3)
                if intguild1DeathsRound3 == playersPerTeamInt:
                    final_winner = 2
                elif intguild2DeathsRound3 == playersPerTeamInt:
                    final_winner = 1
                else:
                    await member.send("Something went wrong in determining the winner of the third round.")
                    return
                
            embed10 = discord.Embed(
                title="War Logging",
                description=f"Please enter who was the MVP Player of this War.",
                color=0x2F3136
            )
            await member.send(embed=embed10)
            mvpmsg = await self.bot.wait_for('message', check=check, timeout=180.0)
            mvp = mvpmsg.content
            if mvp == 'cancel':
                await member.send('Cancelled War-Log.')
                return

            # Calculate the ELO changes
            elo_guild_1 = guild_data["guilds"][guild1]["elo_amount"]
            elo_guild_2 = guild_data["guilds"][guild2]["elo_amount"]
            win_points, lose_points = elo_calculation(elo_guild_1, elo_guild_2, doubleflawless, final_winner)

            if final_winner == 1:
                guild_data["guilds"][guild1]["elo_amount"] += win_points
                guild_data["guilds"][guild2]["elo_amount"] += lose_points
                await self.logging(ctx, f"Added **{win_points} ELO** to {guild1.capitalize()}, **{lose_points} ELO** to {guild2.capitalize()}\n hosted by {ctx.author.mention}", "War Elo")
            else:
                guild_data["guilds"][guild2]["elo_amount"] += win_points
                guild_data["guilds"][guild1]["elo_amount"] += lose_points
                await self.logging(ctx, f"Added **{win_points}** ELO to {guild2.capitalize()}, **{lose_points} ELO** to {guild1.capitalize()}\n hosted by {ctx.author.mention}", "War Elo")
            if guild_data["guilds"][guild1]["elo_amount"] < 0:
                guild_data["guilds"][guild1]["elo_amount"] = 0
            if guild_data["guilds"][guild2]["elo_amount"] < 0:
                guild_data["guilds"][guild2]["elo_amount"] = 0

            flawless = ""
            if doubleflawless:
                flawless = "# *DOUBLE FLAWELESS*"
            blahblah = ""
            if not jetztschon:
                blahblah = f"""
## Round 3
{guild1.capitalize()} deaths: {guild1DeathsRound3}
{guild2.capitalize()} deaths: {guild2DeathsRound3}
                """
            winner = "nein"
            loser = "ja"
            if final_winner == 1:
                winner = guild1.capitalize()
                loser = guild2.capitalize()
            elif final_winner == 2:
                winner = guild2.capitalize()
                loser = guild1.capitalize()

            save_guild_data()
            warlog_content = f"""# {guild1.capitalize()} vs {guild2.capitalize()}\n*hosted by {ctx.author.mention}*
## Round 1
{guild1.capitalize()} deaths: {guild1DeathsRound1}
{guild2.capitalize()} deaths: {guild2DeathsRound1}
## Round 2
{guild1.capitalize()} deaths: {guild1DeathsRound2}
{guild2.capitalize()} deaths: {guild2DeathsRound2}
{blahblah}
## Winner: {winner}
MVP: {mvp}
{winner}: +{win_points} Elo
{loser}: {lose_points} Elo
{flawless}
"""
            await war_log_channel.send(warlog_content)
            await self.logging(ctx, f"Successfully send war log message of war between {guild1.capitalize()} and {guild2.capitalize()}\n hosted by {ctx.author.mention}")

            await member.send("War log has been posted successfully.")


        except asyncio.TimeoutError:	
            await member.send('Timed out. You took too long to answer.')
            return
        
# VIEWS:

class ManagementActionSelector(Select):
    def __init__(self, ctx, guild):
        self.ctx = ctx
        self.guild = guild
        self.logging_channel = ctx.bot.get_channel(logging_channel_id)
        options = [
            discord.SelectOption(label="Transfer Leadership", description="Transfer the Leadership of your Guild. (CANNOT BE UNDONE)"),
            discord.SelectOption(label="Disband Guild", description="Disbands your guild. (CANNOT BE UNDONE)"),
            discord.SelectOption(label="Change Co-Leader", description="Change the Co-Leader of your Guild."),
            discord.SelectOption(label="Change Manager", description="Change the Manager of your Guild.")
        ]
        super().__init__(placeholder='Choose an action...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_action = self.values[0]
        if selected_action == "Transfer Leadership":
            await self.transfer_leadership(interaction)
        elif selected_action == "Disband Guild":
            await self.disband_guild(interaction)
        elif selected_action == "Change Co-Leader":
            await self.change_co_leader(interaction)
        elif selected_action == "Change Manager":
            await self.change_manager(interaction)

    async def transfer_leadership(self, interaction: discord.Interaction):
        await interaction.response.send_message("Please mention the new leader to transfer leadership to:")
        def message_check(m):
            return m.author == self.ctx.author and m.channel == interaction.channel

        try:
            msg = await self.ctx.bot.wait_for('message', check=message_check, timeout=60)
            new_leader = await MemberOrIDConverter().convert(self.ctx, msg.content)
            if new_leader:
                guild = self.guild
                old_leader = int(guild_data["guilds"][guild]["leader"])
                guild_data["guilds"][guild]["leader"] = str(new_leader.id)
                save_guild_data()
                await removeLeader(self.ctx, old_leader)
                await self.ctx.author.send(f"Successfully transferred leadership of guild `{guild.capitalize()}` to {new_leader.mention}.")
                await self.ctx.bot.get_cog('EloSystem').logging(self.ctx, f"Transferred leadership of guild `{guild.capitalize()}` to {new_leader.mention} | {new_leader.id}.", "Transfer Leadership")
        except asyncio.TimeoutError:
            await interaction.followup.send("Leadership transfer timed out. Please try again.")

    async def disband_guild(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Are you sure you want to disband the guild `{self.guild.capitalize()}`?  Type `yes` or `no`:")
        def message_check(m):
            return m.author == self.ctx.author and m.channel == interaction.channel
        try:
            try:
                msg = await self.ctx.bot.wait_for('message', check=message_check, timeout=60)
                if msg.content.lower() == 'yes':
                    old_leader = int(guild_data["guilds"][self.guild]["leader"])
                    co_leader = int(guild_data["guilds"][self.guild]["co_leader"])
                    manager = int(guild_data["guilds"][self.guild]["manager"])
                    await removeLeader(self.ctx, old_leader)
                    await remove_co_manager(self.ctx, co_leader)
                    if manager != 0:
                        await remove_co_manager(self.ctx, manager)
                    del guild_data["guilds"][self.guild]
                    save_guild_data()
                    await self.ctx.author.send(f"Guild `{self.guild.capitalize()}` has been disbanded.")
                    await self.ctx.bot.get_cog('EloSystem').logging(self.ctx, f"Guild `{self.guild.capitalize()}` has been disbanded.", "Disband Guild")
                    await self.logging_channel.send(f"Guild `{self.guild.capital} has been disbanded by {self.ctx.author.mention}, {self.ctx.author.display_name} | {self.ctx.author.id}")
        
                else:
                    await self.ctx.send("Guild disbanding cancelled.")
            except Exception as e:
                    print(e)
        except asyncio.TimeoutError:
            await interaction.followup.send("Guild disbanding timed out. Please try again.")
    async def change_co_leader(self, interaction: discord.Interaction):
        await interaction.response.send_message("Please mention the new co-leader to assign:")
        def message_check(m):
            return m.author == self.ctx.author and isinstance(m.channel, discord.DMChannel)

        try:
            msg = await self.ctx.bot.wait_for('message', check=message_check, timeout=60)
            new_co_leader = await MemberOrIDConverter().convert(self.ctx, msg.content)
            if new_co_leader:
                guild = self.guild
                old_co_leader = int(guild_data["guilds"][guild]["co_leader"])
                guild_data["guilds"][guild]["co_leader"] = str(new_co_leader.id)
                save_guild_data()
                await remove_co_manager(self.ctx, old_co_leader)
                await add_co_manager(self.ctx, new_co_leader.id)
                await self.ctx.author.send(f"Successfully assigned {new_co_leader.mention} as the new co-leader of guild `{guild.capitalize()}`.")
                await self.ctx.bot.get_cog('EloSystem').logging(self.ctx, f"Assigned {new_co_leader.mention} as the new co-leader of guild `{guild.capitalize()}` | {new_co_leader.id}.", "Change Co-Leader")
        except asyncio.TimeoutError:
            await interaction.followup.send("Changing co-leader timed out. Please try again.")

    async def change_manager(self, interaction: discord.Interaction):
        await interaction.response.send_message("Please mention the new manager to assign:")
        def message_check(m):
            return m.author == self.ctx.author and isinstance(m.channel, discord.DMChannel)

        try:
            msg = await self.ctx.bot.wait_for('message', check=message_check, timeout=60)
            new_manager = await MemberOrIDConverter().convert(self.ctx, msg.content)
            if new_manager:
                guild = self.guild
                old_manager = int(guild_data["guilds"][guild]["manager"])
                guild_data["guilds"][guild]["manager"] = str(new_manager.id)
                save_guild_data()
                await remove_co_manager(self.ctx, old_manager)
                await add_co_manager(self.ctx, new_manager.id)
                await self.ctx.author.send(f"Successfully assigned {new_manager.mention} as the new manager of guild `{guild.capitalize()}`.")
                await self.ctx.bot.get_cog('EloSystem').logging(self.ctx, f"Assigned {new_manager.mention} as the new manager of guild `{guild.capitalize()}` | {new_manager.id}.", "Change Manager")
        except asyncio.TimeoutError:
            await interaction.followup.send("Changing manager timed out. Please try again.")


class GuildManagementView(View):
    def __init__(self, ctx, guild):
        super().__init__()
        self.guild = guild
        self.add_item(ManagementActionSelector(ctx, self.guild))

async def setup(bot):
    cmd_prfx = bot.command_prefix
    await bot.add_cog(EloSystem(bot, cmd_prfx)) 

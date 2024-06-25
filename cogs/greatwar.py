import discord
from discord.ext import commands
from discord.ext.commands import MemberConverter, check
from discord.ui import View, Select
from typing import Optional as Optional
import asyncio
import json
from cogs.basecog import BaseCog


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
                if ctx.guild:  # Check if ctx.guild is not None
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
  

def permitted():
    def predicate(ctx):
        role_names = [role.name.lower() for role in ctx.author.roles]
        return 'host' in role_names or 'moderator' in role_names or ctx.author.guild_permissions.administrator or ctx.author.id == 890960794337046532
    return check(predicate)


def channel1():
    def predicate(ctx):
        if not isinstance(ctx.author, discord.Member):
            return False
        return ctx.channel.id == role_giving_channel_id or ctx.author.id == 890960794337046532
    return check(predicate)

def server():
    def predicate(ctx):
        return isinstance(ctx.author, discord.Member)
    return check(predicate)    


confirmation_channel_id = 0
life_counter_channel_id = 0
logging_channel_id = 0
submission_channel_id = 0
role_giving_channel_id = 0
life_counter_message_id = 0

mod1_name = "mod1"
mod2_name = "mod2"
mod3_name = "mod3"

def load_guild_data():
    global guild_data
    try:
        with open("guild_data2.json", "r") as file:
            guild_data = json.load(file)
        # Ensure that points keys exist
        if "points" not in guild_data:
            guild_data["points"] = {"A": 0, "B": 0}
            save_guild_data()
    except FileNotFoundError:
        print("Guild data file not found. Creating a new one.")
        guild_data = {  # Initialize with the desired structure
            "clans": {
                "clan1": {
                    "team": "A"
                }
            },
            "participants": {
                "12512351251251251": {
                    "clan": "clan1"
                }
            },
            "points": {
                "A": 0,  # Initialize points for Team A
                "B": 0   # Initialize points for Team B
            }
        }
        save_guild_data()  # Save the default data to file

# Save guild data to file
def save_guild_data():
    with open("guild_data2.json", "w") as file:
        json.dump(guild_data, file, indent=4)


class GreatWar(BaseCog):
    def __init__(self, bot, cmd_prfx):
        super().__init__(bot, "TypeLeague")
        self.bot = bot
        self.cmd_prfx = cmd_prfx
        self.submitting_clips = {}
        load_guild_data()
        

        # Variables
        self.permsdenied = discord.Embed(
            title='Permission Denied',
            color=0xB32900,
            description="You do not have permission to use this command or can't punish this user."
        )
        asyncio.create_task(self.delayed_setup_channels())

    async def delayed_setup_channels(self):
        await asyncio.sleep(11.0)
        await self.setup_channels()

    async def setup_channels(self):
        # Initialize channel objects
        self.confirmation_channel = self.bot.get_channel(confirmation_channel_id)
        self.life_counter_channel = self.bot.get_channel(life_counter_channel_id)
        print("Channels for GreatWar initialized")

        # Check if any channel object is None and print a warning
        if None in (self.confirmation_channel, self.life_counter_channel):
            print("Warning: Some channels could not be found. Double-check the channel IDs.")

    @staticmethod
    async def convert_channel(ctx, argument):
        try:
            channel = await commands.TextChannelConverter().convert(ctx, argument)
            return channel
        except commands.BadArgument:
            raise commands.BadArgument(f"Channel '{argument}' not found.")
        

    @commands.command(name="setupclan", usage="setupclan [clan] [team]")
    @channel1()
    async def setupclan(self, ctx, clan_name: str, team: str):
        """
        Setup a new clan for a specified team.
        """
        # how do I add a command usage here, not up there HERE so I can use self
        if not isinstance(ctx.author, discord.Member): 
            return "You can only run this command in Servers"
        try:
            clan_name = clan_name.lower()
            team = team.upper()
            if team not in ("A", "B"):
                await self.error(ctx, "Team must be either A or B.")
                return
            if "clans" not in guild_data:  # Check if the guild data contains the "clans" key
                guild_data["clans"] = {}
            guild_data["clans"][clan_name] = {"team": team}  # Update the guild data with the new clan and team
            save_guild_data()  # Save the updated guild data
            
            # Send log message
            await self.logging(ctx, f"Successfully setup `Clan {clan_name}` as a member of `team {team}`.", "Setup Clan")

            await self.answer(ctx, f"Successfully setup `Clan {clan_name.capitalize()}` as a member of `team {team}`.")
        except Exception as e:
            await self.error(ctx, e=e)

    @commands.command(name="changeteam", usage="changeteam [clan]")
    @channel1()
    async def change_team(self, ctx, clan_name: str):
        """
        Changes the team of a specified clan.
        """
        if not isinstance(ctx.author, discord.Member): 
            await self.answer(ctx, "You can only run this command in servers.")
            return

        clan_name = clan_name.lower()
        if "clans" not in guild_data or clan_name not in guild_data["clans"]:
            await self.answer(ctx, "Clan not found or no clans configured.")
            return

        current_team = guild_data["clans"][clan_name].get("team")
        if current_team not in ["A", "B"]:
            await self.answer(ctx, "Team not found for the specified clan.")
            return

        new_team = "B" if current_team == "A" else "A"

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            await self.answer(ctx, f"Are you sure you want to change {clan_name.capitalize()}'s team to {new_team}?\nType 'yes' or 'no' to confirm.")
            response = await self.bot.wait_for('message', check=check, timeout=120.0)
            if response.content.lower() in ['no', 'cancel']:
                await self.answer(ctx, "Successfully cancelled the team-changing process.")
                return
            elif response.content.lower() == 'yes':
                # Perform the team swap
                guild_data["clans"][clan_name]["team"] = new_team
                save_guild_data()
                await self.answer(ctx, f"Clan {clan_name.capitalize()} has successfully been moved to Team {new_team}.")
                await self.logging(ctx, f"Starting to move {clan_name.capitalize()} to Team {new_team}", "Team Change")
                
                # Here we should also handle role assignment if applicable.
                await self.update_clan_roles(ctx, clan_name, new_team)
            else:
                await self.error(ctx, "Invalid response. Please type 'yes' or 'no'.")
        except asyncio.TimeoutError:
            await ctx.send("Cancelled the team-changing process as you didn't respond within 2 minutes.")

    async def update_clan_roles(self, ctx, clan_name, new_team):
        team_role = discord.utils.get(ctx.guild.roles, name=f"Team {new_team}")
        teamA_role = discord.utils.get(ctx.guild.roles, name="Team A")
        teamB_role = discord.utils.get(ctx.guild.roles, name="Team B")
        if not team_role:
            await self.error(ctx, f"Role for Team {new_team} not found.")
            return

        # Example: Iterate through all members and update roles based on clan affiliation
        for member_id, details in guild_data.get("participants", {}).items():
            if details.get("clan") == clan_name:
                member = ctx.guild.get_member(int(member_id))
                if member:
                    # Remove old roles and add new ones as needed
                    await member.remove_roles(teamA_role)
                    await member.remove_roles(teamB_role)
                    await member.add_roles(team_role)
                    await member.send(f"You have been moved to Team {new_team}.")
                    await self.logging(ctx, "Team Change", f"Successfully changed {clan_name.capitalize()}'s team to {new_team}.")


    @commands.command(name="addmember", usage="addmember [member] [clan]")
    @channel1()
    async def addmember(self, ctx, member: discord.Member, clan_name: str):
        """
        Add Member Command: Adds a member to the specified clan.
        """
        if not isinstance(ctx.author, discord.Member):
            return "You can only run this command in Servers"
        clan_name = clan_name.lower()

        # Load guild data
        load_guild_data()

        # Check if the clan exists
        if clan_name not in guild_data.get("clans", {}):
            await self.error(ctx, "Clan not found.")
            return

        # Get the team associated with the clan
        team_name = guild_data["clans"][clan_name].get("team", None)
        if team_name is None:
            await self.error(ctx, "Team not found for the specified clan.")
            return

        # Get the role object for the team
        team_role = discord.utils.get(ctx.guild.roles, name=f"Team {team_name.upper()}")
        if team_role is None:
            await self.error(ctx, "Team role not found.")
            return

        # Assign the role to the member
        try:
            await member.add_roles(team_role)
            await self.answer(ctx, f"Added {member.mention} to clan {clan_name.capitalize()}, team {team_name}.")

            # Update the participants data
            guild_data["participants"][str(member.id)] = {"clan": clan_name}
            save_guild_data()

            # Send log message
            await self.logging(ctx, f"Added {member.mention} to clan {clan_name.capitalize()}, team {team_name}.", "Added Member")

        except discord.Forbidden:
            await self.error(ctx, "I don't have permission to add roles to this member.")


    @commands.command(name="removeclan", usage="removeclan [clan]")
    @channel1()
    async def removeclan(self, ctx, clan_name: str):
        """
        Remove Clan Command: Removes the specified clan.
        """
        if not isinstance(ctx.author, discord.Member): 
            return "You can only run this command in Servers"
        try:
            # Check if the clan exists
            if clan_name not in guild_data.get("clans", {}):
                await self.error(ctx, "Clan not found.")
                return

            # Remove every participant associated with this clan and their roles
            team = guild_data["clans"][clan_name].get("team")
            team_role_name = f"Team {team}"  # Assuming roles are named 'Team A', 'Team B', etc.
            team_role = discord.utils.get(ctx.guild.roles, name=team_role_name)

            # Iterate over all participants
            for user_id, details in list(guild_data["participants"].items()):
                if details["clan"] == clan_name:
                    member = ctx.guild.get_member(int(user_id))
                    if member and team_role:
                        await member.remove_roles(team_role)
                    # Remove the participant from guild_data
                    del guild_data["participants"][user_id]

            # Remove the clan from guild data
            del guild_data["clans"][clan_name]
            save_guild_data()

            # Send log message
            await self.logging(ctx, f"Successfully removed Clan {clan_name}.", "Removed Clan")

            await self.answer(ctx, f"Successfully removed Clan {clan_name}.")
        except Exception as e:
            await self.error("An error occurred while removing the clan.", e=e)


    @commands.command(name="removemember", usage="removemember [member]")
    @channel1()
    async def removemember(self, ctx, member: discord.Member):
        """
        Remove Member Command: Removes a member from their clan.
        """
        if not isinstance(ctx.author, discord.Member):
            return "You can only run this command in Servers"

        # Load guild data
        load_guild_data()

        # Check if the user is in the participants list
        if str(member.id) not in guild_data.get("participants", {}):
            await self.error(ctx, "Member not found.")
            return

        # Get the clan name and their team role
        clan_name = guild_data["participants"][str(member.id)]["clan"]
        team = guild_data["clans"][clan_name].get("team")
        team_role_name = f"Team {team}"  # Assuming roles are named 'Team A', 'Team B', etc.
        team_role = discord.utils.get(ctx.guild.roles, name=team_role_name)

        if member and team_role:
            await member.remove_roles(team_role)

        # Remove the member from the participants list
        del guild_data["participants"][str(member.id)]
        save_guild_data()

        # Send log message
        await self.logging(ctx, f"Successfully removed Member {member.mention} from their clan.", "Removed Member")

        await self.answer(ctx, f"Successfully removed Member {member.mention} from their clan.")

    @commands.command(name="listclans", usage="listclans")
    @permitted()
    async def listclans(self, ctx):
        """
        List Clans Command: Lists all clans categorized by their teams along with member counts.
        """
        if not isinstance(ctx.author, discord.Member):
            await ctx.send("You can only run this command in Servers.")
            return
        # Load guild data
        load_guild_data()
        # Initialize dictionaries to hold clans categorized by teams
        clans_by_team = {"Team A": [], "Team B": []}
        members_by_clan = {}
        # Initialize member count for each clan based on participants
        for user_id, details in guild_data.get("participants", {}).items():
            clan_name = details["clan"]
            if clan_name in members_by_clan:
                members_by_clan[clan_name] += 1
            else:
                members_by_clan[clan_name] = 1

        # Iterate through the clans in guild data and categorize them by team
        for clan_name, data in guild_data.get("clans", {}).items():
            team = data.get("team", None)
            member_count = members_by_clan.get(clan_name, 0)
            clan_info = f"{clan_name.capitalize()} - {member_count} Members"
            if team == "A":
                clans_by_team["Team A"].append(clan_info)
            elif team == "B":
                clans_by_team["Team B"].append(clan_info)

        # Create embeds for each team
        embed_team_a = discord.Embed(title="Team A", color=discord.Color.red())
        for clan_info in clans_by_team["Team A"]:
            embed_team_a.add_field(name=clan_info.split(' - ')[0], value=clan_info.split(' - ')[1], inline=False)

        embed_team_b = discord.Embed(title="Team B", color=discord.Color.blue())
        for clan_info in clans_by_team["Team B"]:
            embed_team_b.add_field(name=clan_info.split(' - ')[0], value=clan_info.split(' - ')[1], inline=False)

        # Send the message with both embeds, if there are clans to show
        if clans_by_team["Team A"] or clans_by_team["Team B"]:
            await ctx.send(embeds=[embed_team_a, embed_team_b])
        else:
            await self.error(ctx, "No clans available to list.")

    @permitted()
    @commands.command(name="claninfo", usage="claninfo [clan]")
    async def clan_info(self, ctx, clan_name: str):
        """
        Displays information about the specified clan.
        """
        load_guild_data()  # Make sure data is loaded
        clan_name = clan_name.lower()

        clan_data = guild_data.get("clans", {}).get(clan_name)
        if not clan_data:
            await self.error(ctx, f"No information found for clan '{clan_name}'.")
            return

        team = clan_data.get("team", "No team assigned")
        members = [member_id for member_id, details in guild_data.get("participants", {}).items() if details.get("clan") == clan_name]
        member_count = len(members)
        member_details = []

        for member_id in members:
            member = ctx.guild.get_member(int(member_id))
            if member:
                member_details.append(f"- {member.display_name} ({member}) | {member.id}")

        embed = discord.Embed(title=clan_name.capitalize(), description=f"Team {team}", color=0x2F3136)
        embed.add_field(name=f"{member_count} Members:", value="\n".join(member_details) if member_details else "No members found")

        await ctx.send(embed=embed)
        await self.logging(ctx, f"Successfully retrieved information for clan '{clan_name}'.", "Clan Info")

    @permitted()
    @commands.command(name="memberinfo", usage="memberinfo [member]")
    async def member_info(self, ctx, member: discord.Member):
        """
        Displays information about the specified member or the author if no member is specified.
        """
        if not member:
            member = ctx.author

        load_guild_data()
        participant_details = guild_data.get("participants", {}).get(str(member.id))

        if not participant_details:
            await self.error(ctx, "This member does not belong to any clan.")
            return

        clan_name = participant_details.get("clan", "No clan")
        clan_data = guild_data.get("clans", {}).get(clan_name, {})
        team = clan_data.get("team", "No team assigned")

        embed = discord.Embed(title=f"{member.display_name} ({member}) | {member.id}", 
                              description=f"Clan: {clan_name.capitalize()}", color=0x2F3136)
        embed.set_footer(text=f"Team {team}")

        await ctx.send(embed=embed)

    # DeepLeague Commands:
    @permitted()
    @commands.command(name="getpoints", usage="getpoints [team]")
    async def getpoints(self, ctx: commands.Context, team: str):
        """
        Retrieves the points of a specified team from the guild data JSON.
        """
        load_guild_data()  # Ensure data is current
        team = team.upper()
        if team in guild_data["points"]:
            await self.answer(ctx, f"Team {team} has {guild_data['points'][team]} points.")
        else:
            await self.error(ctx, f"Team {team} not recognized. Use 'A' or 'B'.")

    @admin()
    @channel1()
    @commands.command(name="addpoints", usage="addpoints [team] [amount]")
    async def addpoints(self, ctx: commands.Context, team: str, amount: float):
        """
        Adds points to a specified team and updates the guild data JSON.
        """
        load_guild_data()  # Reload guild data to ensure it's up-to-date
        team = team.upper()
        if team in guild_data["points"]:
            guild_data["points"][team] += amount
            save_guild_data()
            await self.answer(ctx, f"Added {amount} points to Team {team}. Total now: {guild_data['points'][team]} points.")
            await self.update_life_counter()
            await self.logging(ctx, f"Added {amount} points from Team {team}. Total now: {guild_data['points'][team]} points.", "Point Addition")
        else:
            await self.error(ctx, f"Team {team} not recognized. Use 'A' or 'B'.")

        @commands.command()
        async def manageclans(self, ctx):
            clans = guild_data["clans"].keys()  # Assuming this retrieves clan names
            await ctx.send("Select a clan to manage:", view=ClanManagementView(clans))

    @admin()
    @channel1()
    @commands.command(name="removepoints", usage="removepoints [team] [amount]")
    async def removepoints(self, ctx: commands.Context, team: str, amount: float):
        """
        Adds points to a specified team and updates the guild data JSON.
        """
        load_guild_data()  # Reload guild data to ensure it's up-to-date
        team = team.upper()
        if team in guild_data["points"]:
            guild_data["points"][team] -= amount
            save_guild_data()
            await self.answer(ctx, f"Removed {amount} points from Team {team}. Total now: {guild_data['points'][team]} points.")
            await self.update_life_counter()
            await self.logging(ctx, f"Removed {amount} points from Team {team}. Total now: {guild_data['points'][team]} points.", "Point Removal")
        else:
            await self.error(ctx, f"Team {team} not recognized. Use 'A' or 'B'.")

        @commands.command()
        async def manageclans(self, ctx):
            clans = guild_data["clans"].keys()  # Assuming this retrieves clan names
            await ctx.send("THIS DOESNT WORK")
            await ctx.send("Select a clan to manage:", view=ClanManagementView(clans))

    @commands.command(name="updatelive", usage="updatelive")
    @permitted()
    async def updatelive(self, ctx: commands.Context):
        """
        Updates the life counter with the current points for each team.
        """
        try: 
            await self.update_life_counter()
            await self.answer(ctx, "Life counter updated successfully.")
        except Exception as e:
            await self.error(ctx, f"An error occurred while updating the life counter.", e=e)

    async def update_life_counter(self):
        # Calculate total points for each team
        total_points_team_a = guild_data["points"].get("A", 0)
        total_points_team_b = guild_data["points"].get("B", 0)

        # Create an embed for the life counter
        embed = discord.Embed(
            title="Life Counter",
            description="Keep track of the teams' points.",
            color=0x00ff00
        )
        embed.add_field(name="Team A", value=str(total_points_team_a), inline=True)
        embed.add_field(name="Team B", value=str(total_points_team_b), inline=True)

        # Update the life counter message
        life_counter_message = await self.life_counter_channel.fetch_message(life_counter_message_id)
        await life_counter_message.edit(content=None, embed=embed)

    # Great War Stuff:
    @commands.command(name="gw", usage="gw")
    async def gw(self, ctx: commands.Context):
        """
        Great War Submission Command: DMs user with submission process if DMs enabled and user is in a team.
        """
        if not isinstance(ctx.author, discord.Member): return "You can only run this command in Servers"
        # Check if the user is already submitting a clip
        if ctx.author.id in self.submitting_clips:
            await self.error(ctx=ctx, description="You are already in the process of submitting a clip.", delete_after=5)
            return

        if ctx.channel != self.bot.get_channel(submission_channel_id):
            await self.error(ctx, f"You can only send this command in <#{submission_channel_id}>")
            return
        fortnite = False
        team_role_names = ["Team A", "Team B"]
        for role in ctx.author.roles:
            if role.name in team_role_names:
                fortnite = True
        if not fortnite:
            await self.error(ctx, f'You can only run this command if you are in a team.', delete_after=5)
            await ctx.message.delete()
            return
        clip_link = 'no link'
        grip_type = 'No Grip Type'
        def check(message):
            return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)

        try:
            self.submitting_clips[ctx.author.id] = True
            await ctx.message.delete()
            member = ctx.author
            if member is None: return
            # ------- Message 0
            embed11 = discord.Embed(
                title='Great War Clip Submission.',
                color=0x2F3136,
                description=f'Please select all cases that apply to the SINGLE CLIP that you are submitting.\n**Please enter your clip link.**'
                f'\n\nType `cancel` to stop this process')
            # ------- Response 0
            try:
                await member.send(embed=embed11)
            except discord.Forbidden:
                await self.error(ctx, f'Please turn on your dms in order to proceed. (Rerun command)', delete_after=5, message=f'{ctx.author.mention}')
                return
            await ctx.send(f'{ctx.author.mention}\nCheck your DMs to proceed your clip submission.', delete_after=10)
            response1 = await self.bot.wait_for('message', check=check, timeout=120.0)
            if response1.content.lower() == 'cancel':
                await member.send('Cancelled clip submission.')
                return
            else:
                clip_link = response1.content
            # ------- Message 1
            embed1 = discord.Embed(
                title='Great War Clip Submission',
                color=0x2F3136,
                description=f"Please select all cases that apply to the SINGLE CLIP that you are submitting:\nSay `clanwar` if the clip is a clanwar grip or "
                f"say `overworld` if the clip is a overworld grip.\nSay `wipe` if the clip is a wipe via TYPE://WIPE.\n\nType `cancel` to stop this process")
            # ------- Message 0.1
            embed01 = discord.Embed(
                title='Great War Clip Submission',
                color=0x2F3136,
                description=f"Please type out the CORRECT clan name of your enemy being gripped in the clip.\n\nType `cancel` to stop this process")
            # ------- Response 0.1
            await member.send(embed=embed01)
            response01 = await self.bot.wait_for('message', check=check, timeout=120.0)
            if response01.content.lower() == 'cancel':
                await member.send('Cancelled clip submission.')
                return
            else:
                enemy_clan = response01.content.lower()
            # ------- Response 1
            await member.send(embed=embed1)
            response = await self.bot.wait_for('message', check=check, timeout=120.0)
            if response.content.lower() == 'clanwar':
                grip_type = 'clanwar'
            elif response.content.lower() == 'overworld':
                grip_type = 'overworld'
            elif response.content.lower() == 'wipe':
                grip_type = 'wipe'
            elif response.content.lower() == 'cancel':
                await member.send('Cancelled clip submission.')
                return
            else:
                await member.send("Invalid response. Please read again. (Have to answer in this DM!)")
                return
            # ------ Message 2
            embed2 = discord.Embed(
                title='Great War Clip Submission',
                color=0x2F3136,
                description='Please select all the cases that apply to the SINGLE CLIP that you are submitting. If you obv. troll or try to cheat or sum shit you get banned.'
                '\nIf you somehow accidentally click on the wrong button or sth. then just cancel and do allat again thx.')
            # ------- Button Shit 
            ctxx = ctx
            view = GWSubmission(bot=self.bot, ctx=ctxx, clip_link=clip_link, grip_type=grip_type, enemy_clan=enemy_clan)
            await member.send(embed=embed2, view=view)
        except Exception as e:
            await self.error(ctx, f'An error occurred while trying to submit clip.', e=e)
        finally:
            # Remove the user's ID from the submitting_clips dictionary when done or if an error occurs
            if ctx.author.id in self.submitting_clips:
                del self.submitting_clips[ctx.author.id]


class GWSubmission(View):
    def __init__(self, bot, ctx, clip_link, grip_type, enemy_clan):
        super().__init__()
        self.clip_link = clip_link
        self.grip_type = grip_type
        self.enemy_clan = enemy_clan
        self.ctx = ctx
        self.bot = bot
        self.mod1 = False
        self.mod2 = False
        self.mod3 = False
        self.eventserver = False
        self.onstream = False
        self.confirmation_channel = self.bot.get_channel(confirmation_channel_id)
        self.logging_channel = self.bot.get_channel(logging_channel_id)
        self.life_counter_channel = self.bot.get_channel(life_counter_channel_id)  # this does not matter for now ig


    @discord.ui.button(label=f"{mod1_name}", style=discord.ButtonStyle.grey)
    async def ismod1(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mod1 = True
        await interaction.response.send_message(f'Selected {mod1_name}')

    @discord.ui.button(label=f"{mod2_name}", style=discord.ButtonStyle.grey)
    async def ismod2(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mod2 = True
        await interaction.response.send_message(f'Selected {mod2_name}')

    @discord.ui.button(label=f"{mod3_name}", style=discord.ButtonStyle.grey)
    async def ismod3(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mod3 = True
        await interaction.response.send_message(f'Selected {mod3_name}')

    @discord.ui.button(label='Eventserver', style=discord.ButtonStyle.grey)
    async def iseventserver(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.eventserver = True
        await interaction.response.send_message('Selected Eventserver')

    @discord.ui.button(label='Onstream', style=discord.ButtonStyle.grey)
    async def isonstream(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.onstream = True
        await interaction.response.send_message('Selected Onstream')

    @discord.ui.button(label='Done', style=discord.ButtonStyle.green)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        # call gwconf here
        team = 0
        if self.ctx.author.roles:
            team_role_names = ["Team A", "Team B"]  # Adjust role names as per your server
            for role in self.ctx.author.roles:
                if role.name in team_role_names:
                    if role.name == "Team A":
                        team = 1
                    elif role.name == "Team B":
                        team = 2
                    break
        else:
            print('Something went wrong idk what at line 281 we are')
        # -------
        vieww = GWConfirmation(bot=self.bot, ctx=self.ctx, clip_link=self.clip_link, grip_type=self.grip_type, mod1=self.mod1, mod2=self.mod2,
                                mod3 = self.mod3, eventserver=self.eventserver, onstream=self.onstream, team=team, enemy_clan=self.enemy_clan)

        await self.confirmation_channel.send(f'Clip: {self.clip_link}')
        my_message = await self.confirmation_channel.send(embed=vieww.embed, view=vieww)  # can I somehow get the message id of this message?
        vieww.message = my_message # type: ignore
        await interaction.response.send_message(f'Successfully queued your clip for confirmation.')
        await self.logging_channel.send(f'{self.ctx.author.mention} successfully used gw cmd. Now queued clip for confirmation.')
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Cancelled clip submission.')
        self.stop()


class GWConfirmation(View):
    def __init__(self, bot, ctx, clip_link, grip_type, mod1, mod2, mod3, eventserver, onstream, team, enemy_clan):
        super().__init__(timeout=None)
        message: discord.Message
        self.clip_link = clip_link
        # ALl the shit that gets passed on from the other shitter
        self.team = team
        self.bot = bot
        self.ctx = ctx
        self.clip_link = clip_link
        self.grip_type = grip_type
        self.mod1 = mod1
        self.mod2 = mod2
        self.mod3 = mod3
        self.eventserver = eventserver
        self.onstream = onstream
        self.value = None
        self.enemy_clan = enemy_clan
        if team == 1:
            self.team_ = 'A'
        if team == 2:
            self.team_ = 'B'
        try:
            with open('guild_data2.json', 'r') as file:
                guild_data = json.load(file)
            
            # Retrieve clan information based on the user ID
            self.clan = guild_data.get("participants", {}).get(str(self.ctx.author.id), {}).get("clan")
        except Exception as e:
            print(e)

        # -----
        self.confirmation_channel = self.bot.get_channel(confirmation_channel_id)
        self.logging_channel = self.bot.get_channel(logging_channel_id)
        self.life_counter_channel = self.bot.get_channel(life_counter_channel_id)  # this does not matter for now ig

    @property
    def embed(self):
        # Set the default color to blue (for pending confirmation)
        color = 0x7289DA
        
        # Check if the clip is confirmed or denied and change the color accordingly
        if self.value:
            color = 0x00FF00  # Green color for confirmed clip
        elif self.value is False:
            color = 0xFF0000  # Red color for denied clip
        embed = discord.Embed(title=f"{self.clan} gripped {self.enemy_clan}", color=color)

        embed.add_field(name="Grip Type", value=f"{self.grip_type}", inline=False)
        embed.add_field(name=f"Submitter is in Team {self.team_}", value=f"", inline=False)

        if self.mod1:
            embed.add_field(name=f"{mod1_name} :white_check_mark: ", value="", inline=False)
        if self.mod2:
            embed.add_field(name=f"{mod2_name} :white_check_mark: ", value="", inline=False)
        if self.mod3:
            embed.add_field(name=f"{mod3_name} :white_check_mark: ", value="", inline=False)
        if self.eventserver:
            embed.add_field(name=f"Event Server :white_check_mark: ", value="", inline=False)
        if self.onstream:
            embed.add_field(name="On Stream :white_check_mark: ", value="", inline=False)
        # Add the user mentioned in the footer
        embed.set_footer(text=f"Submitted by: {self.ctx.author.display_name} ({self.ctx.author}) | {self.ctx.author.id}")
        
        return embed


    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        team = 0
        if self.ctx.author.roles:
            team_role_names = ["Team 1", "Team 2", "Team 3"]  # Adjust role names as per your server
            for role in self.ctx.author.roles:
                if role.name in team_role_names:
                    if role.name == "Team A":
                        team = 1
                    elif role.name == "Team B":
                        team = 2
                    break
        else:
            print('Something went wrong idk what at line 382 we are')
        await self.clip_confirmed(team=team, author=interaction.user)
        self.value = True
        await interaction.response.send_message(f'Clip confirmed by {interaction.user.mention}')
        self.stop()

    @discord.ui.button(label='Deny', style=discord.ButtonStyle.red)
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.clip_denied(author=interaction.user)
        self.value = False
        await interaction.response.send_message(f'Clip Denied by {interaction.user.mention}')
        self.stop()

    async def clip_confirmed(self, team, author):
        self.value = True
        points = 0.0  # Initialize base points
        
        # Determine base points based on the grip type
        if self.grip_type == "clanwar":
            points = 1.0
        elif self.grip_type == "overworld":
            points = 3.0
        elif self.grip_type == "wipe":
            points = 30.0
        else:
            print('Unrecognized grip type.')

        # Apply multipliers based on the conditions
        if self.mod1:
            points *= 2
        if self.mod2:
            points *= 4
        if self.mod3:
            points = 0  # This condition sets points to 0 regardless of previous values
        if self.eventserver:
            points *= 2.0
        if self.onstream:
            points *= 1.5
        if points > 60.0:
            points = 60.0

        # Update the guild_data for points
        load_guild_data()  # Reload guild data to ensure it's up-to-date
        team_key = "A" if team == 1 else "B"

        # Add points to the appropriate team
        if team_key in guild_data["points"]:
            guild_data["points"][team_key] += points
        else:
            guild_data["points"][team_key] = points  # If for any reason the key doesn't exist

        try:
            # Save updated guild data
            save_guild_data()
            total_points_team_a = guild_data["points"].get("A", 0)
            total_points_team_b = guild_data["points"].get("B", 0)

            # Create an embed for the life counter
            embed = discord.Embed(
                title="Life Counter",
                description="Keep track of the teams' points.",
                color=0x2F3136
            )
            embed.add_field(name="Team A", value=str(total_points_team_a), inline=True)
            embed.add_field(name="Team B", value=str(total_points_team_b), inline=True)

            # Update the life counter message
            life_counter_message = await self.life_counter_channel.fetch_message(life_counter_message_id)
            await life_counter_message.edit(embed=embed)
        except Exception as e:
            print(e)
        finally:
            # Create an embed for logging
            embed1 = discord.Embed(
                title="GW Clip Confirmed",
                color=0xFF0000,  # Red for alert
                description=f"{author.mention} confirmed clip. Points added: {points}"
            )

            # Send log message
            await self.logging_channel.send(embed=embed1)
            
            # Update the message in confirmation channel
            await self.message.edit(embed=self.embed)   # type: ignore


    async def clip_denied(self, author):
        self.value = False
        embed = discord.Embed(
            title="GW Clip Denied",
            color=0xFF0000,
            description=f"{author.mention} denied clip."
        )
        await self.logging_channel.send(embed=embed)
        await self.message.edit(embed=self.embed) # type: ignore

class ClanSelector(Select):
    def __init__(self, clans):
        options = [
            discord.SelectOption(label=clan, description=f"Manage {clan}") for clan in clans
        ]
        super().__init__(placeholder='Choose a clan to manage...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_clan = self.values[0]
        # Further interaction handling here

class ClanManagementView(View):
    def __init__(self, clans):
        super().__init__()
        self.add_item(ClanSelector(clans))


async def setup(bot):
    cmd_prfx = bot.command_prefix
    await bot.add_cog(GreatWar(bot, cmd_prfx))

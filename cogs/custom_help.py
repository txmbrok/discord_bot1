import discord
from discord.ext import commands
from typing import List

class HelpSelect(discord.ui.Select):
    def __init__(self, command_list: List[commands.Command], prefix):
        options = [
            discord.SelectOption(label=cmd.name, description=cmd.short_doc or "No description", value=cmd.name)
            for cmd in command_list
        ]
        super().__init__(placeholder="Choose a command...", min_values=1, max_values=1, options=options)
        self.command_list = command_list
        self.prefix = prefix

    async def callback(self, interaction: discord.Interaction):
        command_name = self.values[0]
        command = discord.utils.get(self.command_list, name=command_name)
        if not command:
            await interaction.response.send_message("Command not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Command: {self.prefix}{command.name}",
            description=command.help or "No description available.",
            color=0x2F3136
        )
        
        # Add usage and aliases if they exist
        if command.usage:
            embed.add_field(name="Usage", value=f"{self.prefix}{command.usage}", inline=False)
        if command.aliases:
            embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)

        param_types = set()
        param_info = []

        for param in command.clean_params.values():
            param_type = param.annotation.__name__ if hasattr(param.annotation, '__name__') else 'Any'
            if param_type not in param_types:
                param_types.add(param_type)
                param_info.append(f"{param.name}: {param_type}")

        param_info_str = "\n".join(param_info)
        if param_info_str:
            embed.add_field(name="Parameters", value=param_info_str, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

class HelpView(discord.ui.View):
    def __init__(self, command_list: List[commands.Command], prefix):
        super().__init__()
        self.add_item(HelpSelect(command_list, prefix))

class Help(commands.Cog):
    def __init__(self, bot, cmd_prfx):
        self.bot = bot
        self.cmd_prfx = cmd_prfx

    async def send_help_embed(self, ctx):
        guild_prefix = self.cmd_prfx
        embed = discord.Embed(title="Overview", description=f"The prefix for `{ctx.guild.name}` is `{guild_prefix}`", color=0x2F3136)
        commands_by_cog = {}

        for command in self.bot.commands:
            if getattr(command, 'hidden', False):
                continue
            if isinstance(command, commands.Command) and not isinstance(command, commands.Group):
                cog_name = command.cog_name or "Uncategorized"
                if cog_name.lower() == "help":
                    continue
                if cog_name not in commands_by_cog:
                    commands_by_cog[cog_name] = []
                commands_by_cog[cog_name].append(command)

        sorted_commands_by_cog = dict(sorted(commands_by_cog.items(), key=lambda x: len(x[1]), reverse=True))
        for cog_name, cog_commands in sorted_commands_by_cog.items():
            embed.add_field(name=f"**{cog_name}**", value="\n".join(cmd.name for cmd in cog_commands), inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="help", description="Shows help information for commands.")
    async def help_command(self, ctx, *, command_or_category: str = 'fortnite'):
        if command_or_category == 'fortnite' or None:
            await self.send_help_embed(ctx)
            return

        command_or_category = command_or_category.lower()
        cog = next((c for c in self.bot.cogs.values() if c.qualified_name.lower() == command_or_category), None)
        if cog:
            commands = [cmd for cmd in self.bot.commands if cmd.cog_name == cog.qualified_name]
            view = HelpView(commands, self.cmd_prfx)
            await ctx.send(f"Help for category: **{cog.qualified_name}**", view=view)
            return

        cmd = self.bot.get_command(command_or_category)
        if cmd:
            embed = discord.Embed(title=f"Command: {self.cmd_prfx}{cmd.name}",
                                description=cmd.help or "No description available.", color=0x2F3136)
            if cmd.usage:
                embed.add_field(name="Usage", value=f"{self.cmd_prfx}{cmd.usage}", inline=False)
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
            
            # Include parameters
            params = cmd.clean_params
            if params:
                param_details = "\n".join([f"{name}: {param.annotation.__name__ if hasattr(param.annotation, '__name__') else 'Any'}"
                                        for name, param in params.items()])
                embed.add_field(name="Parameters", value=param_details, inline=False)

            await ctx.send(embed=embed)
        else:
            await ctx.send("Command or category not found.")

async def setup(bot):
    cmd_prfx = bot.command_prefix
    await bot.add_cog(Help(bot, cmd_prfx))

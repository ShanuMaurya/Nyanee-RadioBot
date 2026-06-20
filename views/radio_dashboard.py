import discord
import random
from views.station_select import StationView
from services.radio_browser import search
from services.player import FILTERS
from services import db

async def check_permissions(interaction: discord.Interaction):
    if interaction.user.guild_permissions.administrator or interaction.user.id == interaction.guild.owner_id:
        return True
    settings = await db.get_guild_settings(interaction.guild_id)
    if settings and settings['dj_role_id']:
        if discord.utils.get(interaction.user.roles, id=settings['dj_role_id']):
            return True
        await interaction.response.send_message("❌ You need the DJ role to use this.", ephemeral=True)
        return False
    return True # Unrestricted if no DJ role set

class SearchModal(discord.ui.Modal, title='Search Radio Station'):
    query = discord.ui.TextInput(label='Station Name', placeholder='e.g., BBC Radio 1')

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        stations = search(self.query.value)
        if not stations:
            return await interaction.followup.send("No stations found.", ephemeral=True)
        await interaction.followup.send(f'Results for "{self.query.value}":', view=StationView(self.cog, stations))

class FilterSelect(discord.ui.Select):
    def __init__(self, player):
        options = [
            discord.SelectOption(label=name, value=name, default=(name == player.current_filter_name))
            for name in FILTERS.keys()
        ]
        super().__init__(placeholder="Select an Audio Filter...", min_values=1, max_values=1, options=options, row=1)
        self.player = player

    async def callback(self, interaction: discord.Interaction):
        if not await check_permissions(interaction): return
        await interaction.response.defer()
        success = await self.player.set_filter(self.values[0])
        if success:
            embed = self.view.cog.build_dashboard_embed(self.player, self.player.station)
            await interaction.message.edit(embed=embed, view=RadioDashboard(self.player, self.view.cog))

class RadioDashboard(discord.ui.View):
    def __init__(self, player, cog):
        super().__init__(timeout=None)
        self.player = player
        self.cog = cog
        self.add_item(FilterSelect(player))

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹", row=0)
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await check_permissions(interaction): return
        
        settings = await db.get_guild_settings(interaction.guild_id)
        if settings and settings['channel_id']:
            return await interaction.response.send_message("❌ Cannot manually stop the player while 24/7 mode is active. An Admin must use `/disable_24_7`.", ephemeral=True)

        await self.player.disconnect()
        self.cog.players.pop(interaction.guild.id, None)
        for child in self.children: child.disabled = True
        embed = discord.Embed(title="📻 Playback Stopped", color=0x2b2d31)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.secondary, emoji="🔄", row=0)
    async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.player.voice_client or not self.player.voice_client.is_playing() and not self.player.is_paused:
            return await interaction.response.send_message("Nothing is playing.", ephemeral=True)
        embed = self.cog.build_dashboard_embed(self.player, self.player.station)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Search", style=discord.ButtonStyle.primary, emoji="🔍", row=0)
    async def search_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SearchModal(self.cog))
        
    @discord.ui.button(label="Random Top", style=discord.ButtonStyle.success, emoji="🎲", row=0)
    async def random_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        stations = search("pop", limit=50)
        if stations:
            await self.cog.play_station(interaction, random.choice(stations))
        else:
            await interaction.followup.send("Could not fetch a random station.", ephemeral=True)

    @discord.ui.button(label="Favorite", style=discord.ButtonStyle.secondary, emoji="⭐", row=0)
    async def favorite_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        station = self.player.station
        if not station: return await interaction.response.send_message("❌ No station loaded.", ephemeral=True)
        url = station.get('url_resolved') or station.get('url')
        await db.add_favorite(interaction.user.id, station.get('name', 'Unknown'), url)
        await interaction.response.send_message(f"⭐ **{station.get('name')}** added to your favorites!", ephemeral=True)

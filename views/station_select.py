
import discord

class StationSelect(discord.ui.Select):
    def __init__(self, cog, stations, action="play", extra_data=None):
        self.cog = cog
        self.stations = stations
        self.action = action
        self.extra_data = extra_data

        options = [
            discord.SelectOption(
                label=s.get('name','Unknown')[:100],
                value=str(i)
            )
            for i,s in enumerate(stations[:25])
        ]

        super().__init__(placeholder='Choose a station...', options=options)

    async def callback(self, interaction: discord.Interaction):
        station = self.stations[int(self.values[0])]
        if self.action == "play":
            await self.cog.play_station(interaction, station)
        elif self.action == "set_24_7":
            channel_id = self.extra_data['channel_id']
            from services import db
            url = station.get('url_resolved') or station.get('url')
            await db.set_24_7(interaction.guild_id, channel_id, url, station.get('name', 'Unknown'))
            await interaction.response.send_message(f"✅ 24/7 mode enabled! The bot will now automatically play **{station.get('name')}** in <#{channel_id}>.", ephemeral=True)
            self.view.stop()

class StationView(discord.ui.View):
    def __init__(self, cog, stations, action="play", extra_data=None):
        super().__init__(timeout=120)
        self.add_item(StationSelect(cog, stations, action, extra_data))

import discord
import random
from discord.ext import commands, tasks
from discord import app_commands
import traceback
from services.radio_browser import search
from services.player import RadioPlayer
from views.radio_dashboard import RadioDashboard
from services import db
import aiohttp
from shazamio import Shazam

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

def admin_only():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator or interaction.user.id == interaction.guild.owner_id:
            return True
        await interaction.response.send_message("❌ You must be an Administrator to use this command.", ephemeral=True)
        return False
    return app_commands.check(predicate)

class Radio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}
        import datetime
        self.start_time = datetime.datetime.utcnow()
        
    async def cog_load(self):
        await db.init_db()
        self.twenty_four_seven_loop.start()
        self.presence_loop.start()
        
    async def cog_unload(self):
        self.twenty_four_seven_loop.cancel()
        self.presence_loop.cancel()
        for player in self.players.values():
            await player.disconnect()
            
    def get_player(self, guild_id):
        return self.players.get(guild_id)

    def build_dashboard_embed(self, player, station):
        embed = discord.Embed(
            title='📻 Live Radio',
            description=f"**{station.get('name','Unknown')}**",
            color=0x2b2d31
        )
        if station.get('favicon'):
            embed.set_thumbnail(url=station['favicon'])

        track = player._current_track if player._current_track else "Fetching..."
        embed.add_field(name='🔊 Status', value=f"**{track}**", inline=False)
        embed.add_field(name='🌍 Country', value=station.get('country','Unknown'), inline=True)
        embed.add_field(name='🎵 Codec', value=station.get('codec','Unknown'), inline=True)
        embed.add_field(name='📶 Bitrate', value=f"{station.get('bitrate','?')} kbps", inline=True)
        
        embed.set_footer(text=f"Volume: {int(player.volume * 100)}% | Filter: {player.current_filter_name}")
        return embed

    @tasks.loop(minutes=2)
    async def presence_loop(self):
        try:
            active_streams = len([p for p in self.players.values() if p.voice_client and p.voice_client.is_playing()])
            guild_count = len(self.bot.guilds)
            
            statuses = [
                discord.Activity(type=discord.ActivityType.listening, name=f"radio in {guild_count} servers"),
                discord.Activity(type=discord.ActivityType.playing, name="📻 /help | /radio_search"),
                discord.Activity(type=discord.ActivityType.listening, name=f"to {active_streams} active streams")
            ]
            
            await self.bot.change_presence(activity=random.choice(statuses))
        except Exception as e:
            print(f"Error in presence_loop: {e}")

    @presence_loop.before_loop
    async def before_presence(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def twenty_four_seven_loop(self):
        try:
            settings = await db.get_all_24_7_settings()
            for setting in settings:
                guild = self.bot.get_guild(setting['guild_id'])
                if not guild: continue
                channel = guild.get_channel(setting['channel_id'])
                if not channel: continue
                
                player = self.get_player(guild.id)
                if not player:
                    if not guild.voice_client:
                        try:
                            vc = await channel.connect()
                        except Exception as e:
                            print(f"Failed to connect to 24/7 channel {channel.id}: {e}")
                            continue
                    else:
                        vc = guild.voice_client
                        if vc.channel != channel:
                            await vc.move_to(channel)
                    
                    player = RadioPlayer(guild.id, vc)
                    self.players[guild.id] = player
                    station = {'name': setting['station_name'], 'url': setting['station_url']}
                    
                    members = [m for m in channel.members if not m.bot]
                    if len(members) == 0:
                        player.station = station
                        player.pause() 
                    else:
                        await player.play(station=station, ffmpeg_options=FFMPEG_OPTIONS)
                else:
                    if player.voice_client and player.voice_client.channel != channel:
                        await player.voice_client.move_to(channel)
                    
                    if not player.voice_client.is_playing() and not player.is_paused:
                        members = [m for m in channel.members if not m.bot]
                        if len(members) > 0:
                            station = {'name': setting['station_name'], 'url': setting['station_url']}
                            await player.play(station=station, ffmpeg_options=FFMPEG_OPTIONS)
        except Exception as e:
            print(f"Error in twenty_four_seven_loop: {e}")

    @twenty_four_seven_loop.before_loop
    async def before_24_7(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user:
            if not after.channel:
                self.players.pop(member.guild.id, None)
            return

        vc = member.guild.voice_client
        if vc and vc.channel:
            members = [m for m in vc.channel.members if not m.bot]
            player = self.get_player(member.guild.id)
            if player:
                if len(members) == 0 and not player.is_paused:
                    player.pause()
                elif len(members) > 0 and player.is_paused:
                    await player.resume()

    def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        self.bot.loop.create_task(self._log_error(interaction, error))
        
    async def _log_error(self, interaction: discord.Interaction, error: Exception):
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ An error occurred while processing this command.", ephemeral=True)
            else:
                await interaction.followup.send("❌ An error occurred while processing this command.", ephemeral=True)
        except:
            pass

        log_channel = self.bot.get_channel(583172550171820038)
        if log_channel:
            embed = discord.Embed(title="⚠️ Command Error", color=discord.Color.red())
            embed.add_field(name="Command", value=f"/{interaction.command.name}" if interaction.command else "Unknown")
            embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})")
            embed.add_field(name="Guild", value=f"{interaction.guild.name} ({interaction.guild.id})")
            
            tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            embed.description = f"```py\n{tb[-4000:]}\n```"
            try:
                await log_channel.send(embed=embed)
            except:
                pass
        traceback.print_exception(type(error), error, error.__traceback__)

    async def play_station(self, interaction, station):
        settings = await db.get_guild_settings(interaction.guild_id)
        if settings and settings['channel_id']:
            if interaction.response.is_done():
                return await interaction.followup.send(f"❌ This server has 24/7 mode locked to <#{settings['channel_id']}>. An Admin must use `/disable_24_7` before playing other stations.", ephemeral=True)
            return await interaction.response.send_message(f"❌ This server has 24/7 mode locked to <#{settings['channel_id']}>. An Admin must use `/disable_24_7` before playing other stations.", ephemeral=True)

        if not interaction.guild.voice_client:
            if interaction.user.voice:
                vc = await interaction.user.voice.channel.connect()
            else:
                return await interaction.response.send_message("❌ Join a voice channel first.", ephemeral=True)
        else:
            vc = interaction.guild.voice_client

        player = self.get_player(interaction.guild_id)
        if not player:
            player = RadioPlayer(interaction.guild_id, vc)
            self.players[interaction.guild_id] = player
        
        player.voice_client = vc
        embed = self.build_dashboard_embed(player, station)
        view = RadioDashboard(player, self)

        if interaction.response.is_done():
            msg = await interaction.followup.send(embed=embed, view=view, wait=True)
        else:
            await interaction.response.send_message(embed=embed, view=view)
            msg = await interaction.original_response()
            
        try:
            msg = await interaction.channel.fetch_message(msg.id)
        except Exception:
            pass

        await player.play(station, dashboard_message=msg, ffmpeg_options=FFMPEG_OPTIONS)

    @app_commands.command(name='radio_search', description='Search and play a radio station')
    async def search_cmd(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        stations = search(query, limit=25)
        if not stations:
            return await interaction.followup.send("❌ No stations found.")
        
        from views.station_select import StationView
        await interaction.followup.send(
            f"Select a station from the search results for '{query}':",
            view=StationView(self, stations, action="play")
        )

    @app_commands.command(name='radio_nowplaying', description='Show the currently playing station')
    async def nowplaying(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild_id)
        if not player or not player.station:
            return await interaction.response.send_message('Nothing playing.', ephemeral=True)
            
        embed = self.build_dashboard_embed(player, player.station)
        view = RadioDashboard(player, self)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        try:
            msg = await interaction.channel.fetch_message(msg.id)
        except Exception:
            pass
        player.dashboard_message = msg

    @app_commands.command(name='volume', description='Set the radio volume (0-200)')
    async def volume_cmd(self, interaction: discord.Interaction, level: int):
        player = self.get_player(interaction.guild_id)
        if not player:
            return await interaction.response.send_message("❌ Not playing anything.", ephemeral=True)
            
        settings = await db.get_guild_settings(interaction.guild_id)
        if settings and settings['dj_role_id'] and not interaction.user.guild_permissions.administrator:
            if not discord.utils.get(interaction.user.roles, id=settings['dj_role_id']):
                return await interaction.response.send_message("❌ You need the DJ role to change volume.", ephemeral=True)

        player.set_volume(level / 100.0)
        await interaction.response.send_message(f"🔊 Volume set to {level}%.", ephemeral=True)

    @app_commands.command(name='filter', description='Apply an audio filter')
    @app_commands.choices(effect=[
        app_commands.Choice(name="None", value="None"),
        app_commands.Choice(name="Bass Boost", value="Bass Boost"),
        app_commands.Choice(name="Nightcore", value="Nightcore"),
        app_commands.Choice(name="Vaporwave", value="Vaporwave")
    ])
    async def filter_cmd(self, interaction: discord.Interaction, effect: str):
        player = self.get_player(interaction.guild_id)
        if not player:
            return await interaction.response.send_message("❌ Not playing anything.", ephemeral=True)
            
        settings = await db.get_guild_settings(interaction.guild_id)
        if settings and settings['dj_role_id'] and not interaction.user.guild_permissions.administrator:
            if not discord.utils.get(interaction.user.roles, id=settings['dj_role_id']):
                return await interaction.response.send_message("❌ You need the DJ role to change filters.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        await player.set_filter(effect)
        await interaction.followup.send(f"🎧 Filter set to **{effect}**.")

    @app_commands.command(name='help', description='Show all available bot commands')
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📻 Radio Bot Help",
            description="Here are the commands you can use to interact with the radio bot:",
            color=0x2b2d31
        )
        embed.add_field(name="🎧 Public Commands", value=(
            "`/radio_search <query>` - Search and play a radio station.\n"
            "`/radio_nowplaying` - Show the currently playing station.\n"
            "`/volume <0-200>` - Set the radio volume.\n"
            "`/filter <effect>` - Apply an audio filter.\n"
            "`/favorites` - View and play your favorite stations.\n"
            "`/stats` - View the bot's health and system profile.\n"
            "`/help` - Show this message."
        ), inline=False)
        
        if interaction.user.guild_permissions.administrator or interaction.user.id == interaction.guild.owner_id:
            embed.add_field(name="🛡️ Admin Commands", value=(
                "`/set_dj_role <role>` - Restrict control buttons to a specific role.\n"
                "`/set_24_7 <channel> <station>` - Enable 24/7 playback in a channel.\n"
                "`/disable_24_7` - Disable 24/7 mode.\n"
                "`/drag <user>` - Move a user into the bot's voice channel.\n"
                "`/kick <user>` - Disconnect a user from the voice channel."
            ), inline=False)
            
        embed.set_footer(text="Tip: Click the ⭐ button on the dashboard to save favorites!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='whatsong', description='Shazam the currently playing radio stream to find the song name')
    async def whatsong_cmd(self, interaction: discord.Interaction):
        player = self.get_player(interaction.guild_id)
        if not player or not player.station:
            return await interaction.response.send_message("❌ I am not playing anything right now.", ephemeral=True)
            
        await interaction.response.defer()
        url = player.station.get('url_resolved') or player.station.get('url')
        
        import tempfile
        import os
        import asyncio
        
        tmp_name = None
        try:
            # Create a temporary file to store 6 seconds of audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_name = tmp.name
                
            # Use FFmpeg to smoothly capture exactly 6 seconds of the live stream
            process = await asyncio.create_subprocess_exec(
                'ffmpeg', '-y', '-i', url, '-t', '6', '-f', 'mp3', tmp_name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await asyncio.wait_for(process.communicate(), timeout=15.0)
            
            shazam = Shazam()
            out = await shazam.recognize(tmp_name)
            
            if out and 'track' in out:
                track = out['track']
                title = track.get('title', 'Unknown Title')
                artist = track.get('subtitle', 'Unknown Artist')
                image = track.get('images', {}).get('coverarthq')
                url_link = track.get('url', '')
                
                embed = discord.Embed(
                    title="🎵 Song Recognized!",
                    description=f"**{title}**\nby {artist}",
                    color=0x2b2d31,
                    url=url_link if url_link else None
                )
                if image:
                    embed.set_thumbnail(url=image)
                embed.set_footer(text="Powered by Shazam")
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Shazam could not recognize the song. It might be a talk show, or the stream is missing metadata.")
                
        except Exception as e:
            print("Shazam Error:", e)
            await interaction.followup.send("❌ An error occurred while trying to capture the audio stream.")
        finally:
            if tmp_name and os.path.exists(tmp_name):
                try:
                    os.remove(tmp_name)
                except:
                    pass

    @app_commands.command(name='favorites', description='View and play your favorite stations')
    async def favorites_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        favs = await db.get_favorites(interaction.user.id)
        if not favs:
            return await interaction.followup.send("❌ You don't have any favorite stations yet! Click the ⭐ button while listening to save one.")
            
        mock_stations = [{'name': f['name'], 'country': 'Favorite', 'tags': '', 'url_resolved': f['url']} for f in favs]
        
        from views.station_select import StationView
        await interaction.followup.send("⭐ **Your Favorite Stations:**", view=StationView(self, mock_stations))

    @app_commands.command(name='unfavorite', description='Remove a station from your favorites')
    async def unfavorite_cmd(self, interaction: discord.Interaction, station_name: str):
        await db.remove_favorite(interaction.user.id, station_name)
        await interaction.response.send_message(f"🗑️ Removed **{station_name}** from your favorites.", ephemeral=True)

    @unfavorite_cmd.autocomplete('station_name')
    async def unfavorite_autocomplete(self, interaction: discord.Interaction, current: str):
        favs = await db.get_favorites(interaction.user.id)
        return [
            app_commands.Choice(name=f['name'], value=f['name'])
            for f in favs if current.lower() in f['name'].lower()
        ][:25]

    @app_commands.command(name='stats', description='Shows the bot health and system profile')
    async def stats_cmd(self, interaction: discord.Interaction):
        import datetime
        now = datetime.datetime.utcnow()
        uptime_delta = now - self.start_time
        days, remainder = divmod(int(uptime_delta.total_seconds()), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        active_streams = len([p for p in self.players.values() if p.voice_client and p.voice_client.is_playing()])
        total_listeners = sum([len([m for m in p.voice_client.channel.members if not m.bot]) for p in self.players.values() if p.voice_client and p.voice_client.channel])
        
        ping = round(self.bot.latency * 1000)
        
        embed = discord.Embed(color=0x2b2d31)
        embed.set_author(name=f"{self.bot.user.name} | Health Profile", icon_url=self.bot.user.display_avatar.url if self.bot.user.display_avatar else None)
        if self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            
        embed.add_field(
            name="📊 System",
            value=(
                f"`• Uptime   :` **{uptime_str}**\n"
                f"`• Ping     :` **{ping}ms**\n"
                f"`• Version  :` **Nyanee v4.0**\n"
                f"`• Language :` **Python 3.11**"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📻 Network",
            value=(
                f"`• Servers  :` **{len(self.bot.guilds):,}**\n"
                f"`• Streams  :` **{active_streams:,} Active**\n"
                f"`• Users    :` **{total_listeners:,} Listening**"
            ),
            inline=False
        )
        
        embed.set_footer(text="🟢 All systems operational")
        await interaction.response.send_message(embed=embed)

    # --- ADMIN & MANAGEMENT COMMANDS ---
    @app_commands.command(name='set_dj_role', description='Set the DJ role required to control the bot')
    @admin_only()
    async def set_dj_role(self, interaction: discord.Interaction, role: discord.Role):
        await db.set_dj_role(interaction.guild_id, role.id)
        await interaction.response.send_message(f"✅ DJ Role has been set to {role.mention}. Only users with this role can control the bot now.", ephemeral=True)

    @app_commands.command(name='set_24_7', description='Enable 24/7 radio playback in a channel')
    @admin_only()
    async def set_24_7(self, interaction: discord.Interaction, channel: discord.VoiceChannel, station_query: str):
        await interaction.response.defer(ephemeral=True)
        stations = search(station_query, limit=25)
        if not stations:
            return await interaction.followup.send(f"❌ Could not find a station matching '{station_query}'.")
        
        from views.station_select import StationView
        await interaction.followup.send(
            f"Select the exact station to play 24/7 in {channel.mention}:",
            view=StationView(self, stations, action="set_24_7", extra_data={'channel_id': channel.id})
        )

    @app_commands.command(name='disable_24_7', description='Disable 24/7 radio playback')
    @admin_only()
    async def disable_24_7(self, interaction: discord.Interaction):
        await db.disable_24_7(interaction.guild_id)
        await interaction.response.send_message("✅ 24/7 mode disabled.", ephemeral=True)

    @app_commands.command(name='drag', description='Drag a user into the bot\'s voice channel')
    async def drag_user(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.user.guild_permissions.move_members:
            return await interaction.response.send_message("❌ You do not have permission to move members.", ephemeral=True)
        if not interaction.guild.voice_client or not interaction.guild.voice_client.channel:
            return await interaction.response.send_message("❌ I am not in a voice channel.", ephemeral=True)
        if not user.voice or not user.voice.channel:
            return await interaction.response.send_message(f"❌ {user.display_name} is not in a voice channel.", ephemeral=True)
            
        bot_channel = interaction.guild.voice_client.channel
        await user.move_to(bot_channel)
        await interaction.response.send_message(f"✅ Dragged {user.display_name} into {bot_channel.name}.", ephemeral=True)

    @app_commands.command(name='kick', description='Kick a user from the voice channel')
    async def kick_user(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.user.guild_permissions.move_members:
            return await interaction.response.send_message("❌ You do not have permission to disconnect members.", ephemeral=True)
        if not user.voice or not user.voice.channel:
            return await interaction.response.send_message(f"❌ {user.display_name} is not in a voice channel.", ephemeral=True)
            
        await user.move_to(None)
        await interaction.response.send_message(f"✅ Disconnected {user.display_name}.", ephemeral=True)

    @app_commands.command(name='settings', description='View the current bot settings for this server')
    @admin_only()
    async def settings_cmd(self, interaction: discord.Interaction):
        settings = await db.get_guild_settings(interaction.guild_id)
        embed = discord.Embed(title="⚙️ Server Settings", color=0x2b2d31)
        if not settings:
            embed.description = "No custom settings configured."
        else:
            dj_role = f"<@&{settings['dj_role_id']}>" if settings['dj_role_id'] else "None"
            channel = f"<#{settings['channel_id']}>" if settings['channel_id'] else "None"
            station = settings['station_name'] if settings['station_name'] else "None"
            embed.add_field(name="🎧 DJ Role", value=dj_role, inline=False)
            embed.add_field(name="🔄 24/7 Channel", value=channel, inline=True)
            embed.add_field(name="📻 24/7 Station", value=station, inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Radio(bot))

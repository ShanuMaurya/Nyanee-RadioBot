import discord
import asyncio
from services.metadata import get_current_song

# Pre-defined FFmpeg filters
FILTERS = {
    "None": None,
    "Bass Boost": "bass=g=15",
    "Nightcore": "asetrate=44100*1.25,aresample=44100,atempo=1.25",
    "Vaporwave": "asetrate=44100*0.8,aresample=44100,atempo=0.8"
}

# High quality resampling and mild compression to boost radio streams
HQ_BASE_FILTER = "aresample=resampler=soxr:precision=33,acompressor"

class RadioPlayer:
    def __init__(self, guild_id: int, voice_client: discord.VoiceClient):
        self.guild_id = guild_id
        self.voice_client = voice_client
        self.station = None
        self.dashboard_message = None
        self._metadata_task = None
        self._current_track = "Fetching..."
        
        # Audio enhancement states
        self.volume = 1.0
        self.current_filter_name = "None"
        self._base_ffmpeg_options = None
        self.is_paused = False

    async def play(self, station: dict = None, dashboard_message: discord.Message = None, ffmpeg_options: dict = None):
        if station:
            self.station = station
        if dashboard_message:
            self.dashboard_message = dashboard_message
        if ffmpeg_options is not None:
            self._base_ffmpeg_options = ffmpeg_options

        if not self.station:
            return

        url = self.station.get('url_resolved') or self.station.get('url')
        
        if self.voice_client.is_playing():
            self.voice_client.stop()

        # Prepare FFmpeg options with HQ base filters + optional user filters
        options = dict(self._base_ffmpeg_options or {})
        existing_options = options.get('options', '')
        
        active_filter = HQ_BASE_FILTER
        user_filter = FILTERS.get(self.current_filter_name)
        if user_filter:
            active_filter += f",{user_filter}"
            
        options['options'] = f"{existing_options} -af \"{active_filter}\""

        # Create audio source and wrap with PCMVolumeTransformer for instant volume changes
        try:
            source = discord.FFmpegPCMAudio(url, **options)
            volume_source = discord.PCMVolumeTransformer(source, volume=self.volume)
            self.voice_client.play(volume_source)
            self._start_metadata_polling()
            
            # Initial UI update
            await self._update_ui()
        except Exception as e:
            print(f"Error starting playback: {e}")

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(volume, 2.0)) # Clamp between 0 and 200%
        if self.voice_client and self.voice_client.source and isinstance(self.voice_client.source, discord.PCMVolumeTransformer):
            self.voice_client.source.volume = self.volume
            # Trigger a UI update to refresh the volume display
            asyncio.create_task(self._update_ui())

    async def set_filter(self, filter_name: str):
        if filter_name not in FILTERS:
            return False
        self.current_filter_name = filter_name
        if self.station: # If a station is loaded, restart the stream to apply the filter
            await self.play()
        return True

    def stop(self):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
        self._stop_metadata_polling()

    def pause(self):
        self.is_paused = True
        self.stop()

    async def resume(self):
        if self.is_paused and self.station:
            self.is_paused = False
            await self.play()

    async def disconnect(self):
        self.stop()
        self.is_paused = False
        if self.voice_client:
            try:
                # Clear Voice Channel Status on disconnect
                if hasattr(self.voice_client.channel, 'edit'):
                    await self.voice_client.channel.edit(status=None)
            except:
                pass
            await self.voice_client.disconnect()

    def _start_metadata_polling(self):
        self._stop_metadata_polling()
        self._metadata_task = asyncio.create_task(self._poll_metadata())

    def _stop_metadata_polling(self):
        if self._metadata_task:
            self._metadata_task.cancel()
            self._metadata_task = None

    async def _poll_metadata(self):
        try:
            url = self.station.get('url_resolved') or self.station.get('url')
            while True:
                await asyncio.sleep(15)  # Poll every 15 seconds
                
                if not self.voice_client.is_playing():
                    continue

                track_name = await asyncio.to_thread(get_current_song, url)
                
                if track_name and track_name != self._current_track:
                    self._current_track = track_name
                    await self._update_ui()
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in metadata polling task for guild {self.guild_id}: {e}")

    async def _update_ui(self):
        # 1. Update Voice Channel Status
        if self.voice_client and hasattr(self.voice_client.channel, 'edit'):
            try:
                # Truncate to Discord's status limit of 500 chars (play it safe at 100)
                status_text = f"📻 {self._current_track}"[:100]
                await self.voice_client.channel.edit(status=status_text)
            except discord.Forbidden:
                pass # Bot lacks permission to set voice channel status
            except Exception as e:
                print(f"Failed to update Voice Channel Status: {e}")

        # 2. Update Dashboard Embed
        if self.dashboard_message:
            try:
                if self.dashboard_message.embeds:
                    embed = self.dashboard_message.embeds[0]
                    # Update the "Status" field
                    for i, field in enumerate(embed.fields):
                        if 'Status' in field.name:
                            embed.set_field_at(i, name='🔊 Status', value=f"**{self._current_track}**", inline=False)
                            break
                    
                    embed.set_footer(text=f"Volume: {int(self.volume * 100)}% | Filter: {self.current_filter_name}")
                    await self.dashboard_message.edit(embed=embed)
            except Exception as e:
                print(f"Failed to update dashboard embed: {e}")

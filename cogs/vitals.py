import discord
from discord.ext import commands, tasks
import psutil
import datetime
import time

class Vitals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dashboard_channel_id = 1517781235081154621
        self.dashboard_message = None
        self.start_time = time.time()
        self.vitals_loop.start()

    def cog_unload(self):
        self.vitals_loop.cancel()

    def get_vitals_embed(self):
        cpu_usage = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        mem_usage = mem.percent
        mem_used_mb = mem.used / (1024 * 1024)
        mem_total_mb = mem.total / (1024 * 1024)
        
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        disk_free_gb = disk.free / (1024 * 1024 * 1024)

        uptime_seconds = int(time.time() - self.start_time)
        uptime_string = str(datetime.timedelta(seconds=uptime_seconds))

        ping = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🖥️ Server Vitals Dashboard",
            color=discord.Color.brand_green(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="Memory Usage", value=f"{mem_usage}%\n({mem_used_mb:.1f} MB / {mem_total_mb:.1f} MB)", inline=True)
        embed.add_field(name="Disk Free", value=f"{disk_free_gb:.1f} GB ({disk_usage}% used)", inline=True)
        
        embed.add_field(name="Bot Latency", value=f"{ping} ms", inline=True)
        embed.add_field(name="Bot Uptime", value=f"{uptime_string}", inline=True)

        embed.set_footer(text="Live updating every 60 seconds")
        return embed

    @tasks.loop(minutes=1)
    async def vitals_loop(self):
        await self.bot.wait_until_ready()
        
        channel = self.bot.get_channel(self.dashboard_channel_id)
        if not channel:
            return

        embed = self.get_vitals_embed()

        if self.dashboard_message is None:
            # Try to fetch recent messages to see if we already have a dashboard message here
            try:
                async for msg in channel.history(limit=10):
                    if msg.author == self.bot.user and msg.embeds and msg.embeds[0].title == "🖥️ Server Vitals Dashboard":
                        self.dashboard_message = msg
                        break
            except Exception:
                pass

        if self.dashboard_message is None:
            try:
                self.dashboard_message = await channel.send(embed=embed)
            except Exception as e:
                print(f"Failed to send vitals dashboard: {e}")
        else:
            try:
                await self.dashboard_message.edit(embed=embed)
            except discord.NotFound:
                # Message was deleted, send a new one
                try:
                    self.dashboard_message = await channel.send(embed=embed)
                except Exception:
                    pass
            except Exception as e:
                print(f"Failed to edit vitals dashboard: {e}")

    @vitals_loop.before_loop
    async def before_vitals_loop(self):
        # Initialize CPU percent
        psutil.cpu_percent(interval=0.1)
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Vitals(bot))

import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import os
from dotenv import load_dotenv
import nacl
import asyncio
import youtube_dl


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

load_dotenv()

DISCORD_TOKEN = os.getenv("discord_token")
FFMPEG_EXECUTABLE_PATH = os.getenv("ffmpeg_executable_path")
intents = discord.Intents().all()
bot = commands.Bot(command_prefix='!', intents=intents)


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(executable=FFMPEG_EXECUTABLE_PATH, source="Muney.mp3"), data=data)


@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()


@bot.command(name='m')
async def enter(ctx):
    connected = ctx.author.voice
    if not connected:
        await ctx.send("You need to be connected in a voice channel to use this command!")

    await connected.channel.connect()
    player = await YTDLSource.from_url('https://www.youtube.com/watch?v=IBfJFVIwSJo')
    ctx.voice_client.play(player,  after=lambda _: asyncio.run_coroutine_threadsafe(
        coro=ctx.voice_client.disconnect(),
        loop=ctx.voice_client.loop
    ).result()
)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)

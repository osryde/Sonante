import discord
import yt_dlp
import asyncio
import re

from discord.ext import commands

# Intents grant the bot access to certain events and data
intents = discord.Intents.default()
intents.members = True  
intents.guilds = True 
intents.message_content = True # Grants access to message content

# Commands are called by prefixing the command name with the prefix
bot = commands.Bot(command_prefix="!", intents=intents)

# Queue to store the songs
queue = []

async def play_audio(ctx, url):
    """Grant connection to the voice channel and plays the audio."""
    
    # Verify if the user who sent the command is in a voice channel
    if not ctx.author.voice:
        await ctx.send("❌ Devi essere in un canale vocale per riprodurre musica! ❌")
        return

    import re

    # Verify if the link is a valid suno link
    suno_match = re.match(r"https://suno\.com/song/([a-f0-9\-]+)", url)
    #youtube_match = re.match(r"https://www\.youtube\.com/watch\?v=([a-zA-Z0-9\-_]+)", url)
    #youtu_be_match = re.match(r"https://youtu\.be/([a-zA-Z0-9\-_]+)", url)

    if not suno_match:
        await ctx.send("❌ Sono accettati solo link di suno!")
        return

    if suno_match:
        song_id = suno_match.group(1)  # Estrai solo l'ID del brano
        url = f"https://cdn1.suno.ai/{song_id}.mp3"

    voice_channel = ctx.author.voice.channel

    # Verify if the bot is already connected to a voice channel
    if ctx.voice_client:
        if ctx.voice_client.channel != voice_channel:
            await ctx.voice_client.disconnect() 
            await asyncio.sleep(1) # wait for the bot to disconnect

    # If the bot is not connected to a voice channel 
    if not ctx.voice_client: 
        vc = await voice_channel.connect()
    else:
        vc = ctx.voice_client

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True
    }

    # Extract the audio link with yt-dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        audio_url = info['url']

    # Plays the audio
    vc.play(discord.FFmpegPCMAudio(audio_url, executable="ffmpeg"), after=lambda e: asyncio.run_coroutine_threadsafe(auto_disconnect(ctx, vc), bot.loop))    
    
    while vc.is_playing():
        await asyncio.sleep(1)
    
    # Play the next song in the queue  
    await play_next(ctx)
        
async def auto_disconnect(ctx, vc):
    """Disconnect the bot if nothing is playing."""
    await asyncio.sleep(10)
    if not vc.is_playing():
        await vc.disconnect()
        await ctx.send("👋 Sono uscito dal canale!")

async def play_next(ctx):
    """Play the next song in the queue."""
    if queue:
        await play_audio(ctx, queue.pop(0))
    else:
        await ctx.voice_client.disconnect()  # Se non ci sono brani, disconnessione
        await ctx.send("👋 Sono uscito dal canale!")
        

@bot.event
async def on_ready():
    print(f'✅ Bot connesso come {bot.user}')

# ===== Command Handlers =====

@bot.command()
async def play(ctx, url):
    """Reproduce song from a suno link."""

    if not ctx.guild:  
        await ctx.send("❌ Questo comando può essere usato solo in un server!")
        return

    if not ctx.author.voice:  
        await ctx.send("❌ Devi essere in un canale vocale per usare questo comando!")
        return

    # Add the song to the queue
    queue.append(url)

    # If the bot is not playing anything, play the song
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await play_audio(ctx, queue.pop(0))

@bot.command()
async def leave(ctx):
    """Disconnect the bot from the voice channel."""
    if not ctx.guild:  # Commands can only be used in a server
        await ctx.send("❌ Questo comando può essere usato solo in un server!")
        return

    if not ctx.author.voice:  # If the user is not in a voice channel
        await ctx.send("❌ Devi essere in un canale vocale per usare questo comando!")
        return

    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Sono uscito dal canale!")
        queue.clear()  # Clears the queue
    else:
        await ctx.send("❌ Non sono in nessun canale vocale!")

@bot.command()
async def stop(ctx):
    """Stop the audio."""
    if not ctx.guild:
        await ctx.send("❌ Il bot non è in nessun canale!")

    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏹️ Audio fermato!")
        queue.clear()
        await ctx.voice_client.disconnect()

@bot.command()
async def skip(ctx):
    """Skip the current audio."""
    if not ctx.guild:
        await ctx.send("❌ Il bot non è in nessun canale!")
        return

    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("⏭️ Audio saltato!")
        

# Run the bot
bot.run("DISCORD_TOKEN")

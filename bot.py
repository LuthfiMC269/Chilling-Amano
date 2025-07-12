#import requirements
import subprocess
import asyncio
import os
import re
import sys
import yt_dlp
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from urllib.parse import urlparse

"""ENV LOAD"""
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') #Masukin Token BOT DISCORD DISINI
PREFIX = os.getenv('BOT_PREFIX', '.') #Prefix manggil bot di Discord default titik (.)
BOT_REPORT_DL_ERROR = os.getenv('BOT_REPORT_DL_ERROR', '0').lower() in ('true', 't', '1')
guildid = int(os.getenv('TESTING_GUILD_ID')) #Id guild untuk testing
"""END ENV LOAD"""
bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all()) #define bot
bot.remove_command('help')
queues = {} #antrian playlist

"""STARTUP"""
def main():
    if TOKEN is None:
        return "tidak ada token terdeteksi. buat file copy .example env > .env dan masukkan token bot discord kamu"
    try: bot.run(TOKEN)
    except discord.PrivilegedIntentsRequired as error1:
        return error1

@bot.event
async def on_ready():
    test_guild = discord.Object(id=guildid) #debugging di test guild
    try:
        synced = await bot.tree.sync(guild=test_guild) #sinkronisasi instant ke test guild
        print(f"synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"error sync command: {e}")
    print(f'berhasil login dengan nama bot: {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening,
                                                        name=f'{PREFIX}play 🎵 | {get_git_version()}'))
"""COMMAND BOT START DISINI"""
@bot.hybrid_command(name='play', aliases=['p'], description="Putar musik dari search youtube")
@app_commands.describe(query="Judul atau link musik dari youtube")
@app_commands.guilds(discord.Object(id=guildid))
async def play(ctx: commands.Context, query: str):
    await ctx.send("testing hybrid command")

"""DEF FUNCTION MULAI DISINI"""
def after_track(error3, connection, serverid, ctx): #Lanjut ke queue selanjutnya, atau udahan
    if error3 is not None:
        print(error3)
    try:
        last_video_path = queues[serverid]['queue'][0][0]
        if not queues[serverid]['loop']:
            os.remove(last_video_path)
            queues[serverid]['queue'].pop(0)
    except KeyError: return

    if last_video_path not in [i[0] for i in queues[serverid]['queue']]:
        try: os.remove(last_video_path)
        except FileNotFoundError:
            pass
    try:
        next_path, next_data = queues[serverid]['queue'][0]
        def after_func(error4=None):
            after_track(error4, connection, serverid, ctx)
        connection.play(discord.FFmpegOpusAudio(next_path), after=after_func)
        coro = send_now_playing_embed(ctx, next_data)
        asyncio.run_coroutine_threadsafe(coro, bot.loop)
    except IndexError: #Kalo Antrian habis, bot kelar
        queues.pop(serverid) # delete direktori serverid
        asyncio.run_coroutine_threadsafe(disconnect(connection), bot.loop).result() #disconnect

async def disconnect(connection):
    if not connection.is_playing():
        await connection.disconnect()

async def uservoice_check(ctx: commands.Context, voice_state=None) -> bool: #cek apa user ada di voice channel?
    if voice_state is None:
        voice_state = ctx.author.voice
    if voice_state is None:
        await ctx.send('Kamu harus masuk voice channel dulu yaa sebelum memakai command ini')
        return False

    bot_voice = ctx.guild.voice_client
    if bot_voice and bot_voice.channel != ctx.author.voice.channel:
        await ctx.send('Kamu harus masuk di voice channel yang sama denganku dulu yaa.')
        return False
    return True

def durasi_fix(s): #ngefix format durasi dari output data["duration"]
    detik = s % 3600
    menit = detik // 60
    detik = detik % 60
    return "%02d:%02d" % (menit, detik)

async def send_now_playing_embed(ctx, data): #NOW PLAYING untuk antrian 2 keatas
    embed = discord.Embed(
        color=discord.Color.green(),
        title='NOW PLAYING:',
        description=f'### {data["title"]}. Durasi {durasi_fix(data["duration"])}')
    embed.set_image(url=data['thumbnail'])
    embed.set_author(name=data['uploader'], icon_url=bot.user.avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

async def notify_error(ctx: commands.Context, err: yt_dlp.utils.DownloadError):
    if BOT_REPORT_DL_ERROR:
        # remove shell colors for discord message
        sanitized = re.compile(r'\x1b[^m]*m').sub('', err.msg).strip()
        if sanitized[0:5].lower() == "error":
            # if message starts with error, strip it to avoid being redundant
            sanitized = sanitized[5:].strip(" :")
        await ctx.send('Error Memutar Lagu! 💀: {}'.format(sanitized))
    else:
        await ctx.send('Maaf gagal memutar lagu 😓')
    return

def get_git_version():
    try:
        subprocess.check_call(['git', 'fetch'])
        version = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').strip()
        updatever = subprocess.check_output(['git', 'rev-parse','--short', 'origin/slash']).decode('utf-8').strip() #compare ke branch slash
    except Exception as e:
        return "version unknown"
    if version != updatever:
        return f"Ver. {version} 🚨 Update baru tersedia!"
    else:
        return f" Ver. {version} latest"

"""BOT DIBUAT OLEH LuthfiMC269:) check me out di https://github.com/LuthfiMC269/Chilling-Amano"""
if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemError as error:
        if True:
            raise
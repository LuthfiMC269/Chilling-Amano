#import requirements
import asyncio
import re
import sys
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yt_dlp
from urllib.parse import urlparse

"""ENV LOAD"""
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') #Masukin Token BOT DISCORD DISINI
PREFIX = os.getenv('BOT_PREFIX', '.') #Prefix manggil bot di Discord default titik (.)
BOT_REPORT_DL_ERROR = os.getenv('BOT_REPORT_DL_ERROR', '0').lower() in ('true', 't', '1')

""""""
bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents(voice_states=True, guilds=True, guild_messages=True, message_content=True))
#define bot dc
queues = {} #antrian playlist

"""STARTUP"""
def main():
    if TOKEN is None:
        return "tidak ada token terdeteksi. buat file copy .example env > .env dan masukkan token bot discord kamu"
    try: bot.run(TOKEN)
    except discord.PrivilegedIntentsRequired as error:
        return error

@bot.event
async def on_ready():
    print(f'logged in successfully as {bot.user.name}')

"""COMMAND BOT START DISINI"""
@bot.command(name='play', aliases=['p'])
async def play(ctx: commands.Context, *args):
    voice_state = ctx.author.voice
    if not await sense_checks(ctx, voice_state=voice_state):
        return

    judul = ' '.join(args)
    shorts_pattern = r"(https?://)?(www\.)?youtube\.com/shorts/"
    if re.search(shorts_pattern, judul):
        await ctx.send("❌ Jangan pake youtube short yaaa") #Ngeblokir YT SHORTS, entah kenapa error
        return
    kalo_input_judul = not not urlparse(judul).scheme

    serverid = ctx.guild.id
    if kalo_input_judul:
        await ctx.send('Membuka link...')
    else:
        await ctx.send(f'Mencari judul `{judul}`...')
    with yt_dlp.YoutubeDL({'format': 'bestaudio', #config search dan download
                           'source_address': '0.0.0.0',
                           'default_search': 'ytsearch',
                           'outtmpl': '%(id)s.mp4',
                           'noplaylist': True,
                           'allow_playlist_files': False,
                           'paths': {'home': f'./dl/{serverid}',}}) as ydl:
        try:
            data = ydl.extract_info(judul, download=False)
            if '/shorts/' in data.get('webpage_url', ''):  # Ngeblokir YT SHORTS, entah kenapa error
                await ctx.send(
                    "❌ Mesin pencari menemukan link YTShort yang tidak didukung. cari dengan keyword lain atau kirim link youtube")
                return
        except yt_dlp.utils.DownloadError as err:
            await notify_about_failure(ctx, err)
            return
        if 'entries' in data:
            data = data['entries'][0]
    url = f'https://www.youtube.com/watch?v={data["id"]}'
    queue = queues.get(serverid, {}).get('queue', [])
    if len(queue) >= 1:
        await ctx.send(f'Masuk antrian! {data["title"]}. Durasi {durasi_fix(data["duration"])}. ')
    try:
        ydl.download(url) # Mulai Download, ambil link dari extraksi data 'id' ke variabel url
    except yt_dlp.utils.DownloadError as err:
        await notify_about_failure(ctx, err)
        return
    path = f'./dl/{serverid}/{data["id"]}.mp4'
    try:
        queues[serverid]['queue'].append((path, data))
    except KeyError:  # queue pertama
        queues[serverid] = {'queue': [(path, data)], 'loop': False}
        try: connection = await voice_state.channel.connect()
        except discord.ClientException:
            connection = get_voice_client_from_channel_id(voice_state.channel.id)
        connection.play(discord.FFmpegOpusAudio(path),
                        after=lambda error=None, server_id=serverid:
                        after_track(error, connection, server_id, ctx))
        embed = discord.Embed(color=discord.Color.green(),  # NOW PLAYING, tapi cuma untuk queue pertama
                              title=f'NOW PLAYING: ',
                              description=f'### {data["title"]}. Durasi {durasi_fix(data["duration"])}'
                              )
        embed.set_image(url=data['thumbnail'])
        embed.set_author(name=data['uploader'], icon_url=bot.user.avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

@bot.command(name='skip', aliases=['s'])
async def skip(ctx: commands.Context, *args):
    serverid = ctx.guild.id

    if serverid not in queues:
        await ctx.send("Tidak ada yang sedang diputar.. 😕")
        return

    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is None or not voice_client.is_playing():
        await ctx.send("Tidak ada yang sedang diputar.. 😕")
        return

    # .skip all
    if args and args[0].lower() == 'all':
        try:
            # Stop dan hapus semua file
            for path, _ in queues[serverid]['queue']:
                try: os.remove(path)
                except FileNotFoundError: pass
        except KeyError:
            pass

        queues.pop(serverid, None)
        await voice_client.disconnect()
        await ctx.send("⏹️ Skip semua antrian.")
        return

    # .skip biasa
    queue = queues.get(serverid, {}).get('queue', [])
    if len(queue) <= 1:
        # Cuma ada 1 lagu atau kosong
        voice_client.stop()
        await ctx.send("⏹️ Skip lagu, tidak ada antrian lagi.")
    else:
        await ctx.send("⏭️ Skip lagu, lanjut ke antrian berikut.")
        voice_client.stop()

@bot.command('loop', aliases=['l'])
async def loop(ctx: commands.Context):
    if not await sense_checks(ctx):
        return
    try:
        loop = queues[ctx.guild.id]['loop']
    except KeyError:
        await ctx.send('Aku lagi ga pasang lagu apapun 😕')
        return
    queues[ctx.guild.id]['loop'] = not loop

    await ctx.send('Looping ' + ('dinyalakan' if not loop else 'dimatikan'))

"""DEF FUNCTION MULAI DISINI"""
def get_voice_client_from_channel_id(channel_id: int):
    for voice_client in bot.voice_clients:
        if voice_client.channel == channel_id:
            return voice_client

def after_track(error, connection, serverid, ctx): #Lanjut ke queue selanjutnya, atau udahan
    if error is not None:
        print(error)
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
        def after_func(error=None):
            after_track(error, connection, serverid, ctx)
        connection.play(discord.FFmpegOpusAudio(next_path), after=after_func)
        coro = send_now_playing_embed(ctx, next_data)
        asyncio.run_coroutine_threadsafe(coro, bot.loop)

    except IndexError: #Kalo Antrian habis, bot kelar
        queues.pop(serverid) # delete direktori serverid
        asyncio.run_coroutine_threadsafe(safe_disconnect(connection), bot.loop).result() #disconnect

async def safe_disconnect(connection):
    if not connection.is_playing():
        await connection.disconnect()

async def sense_checks(ctx: commands.Context, voice_state=None) -> bool: #cek apa user ada di voice channel?
    if voice_state is None:
        voice_state = ctx.author.voice
    if voice_state is None:
        await ctx.send('you have to be in a voice channel to use this command')
        return False

    if bot.user.id not in [member.id for member in ctx.author.voice.channel.members] and ctx.guild.id in queues.keys():
        await ctx.send('you have to be in the same voice channel as the bot to use this command')
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
        description=f'### {data["title"]}. Durasi {durasi_fix(data["duration"])}'
    )
    embed.set_image(url=data['thumbnail'])
    embed.set_author(name=data['uploader'], icon_url=bot.user.avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

async def notify_about_failure(ctx: commands.Context, err: yt_dlp.utils.DownloadError):
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

if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemError as error:
        if True:
            raise

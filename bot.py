#import requirements
import asyncio
import os
import re
import sys
from urllib.parse import urlparse
import discord
import yt_dlp
from discord.ext import commands
from dotenv import load_dotenv

"""ENV LOAD"""
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') #Masukin Token BOT DISCORD DISINI
PREFIX = os.getenv('BOT_PREFIX', '.') #Prefix manggil bot di Discord default titik (.)
BOT_REPORT_DL_ERROR = os.getenv('BOT_REPORT_DL_ERROR', '0').lower() in ('true', 't', '1')
"""END ENV LOAD"""

bot = commands.Bot(command_prefix=PREFIX, #define bot dc
                   intents=discord.Intents(voice_states=True, guilds=True, guild_messages=True, message_content=True))
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
    print(f'berhasil login dengan nama bot: {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'{PREFIX}play 🎵'))

"""COMMAND BOT START DISINI"""
@bot.command(name='play', aliases=['p'])
async def play(ctx: commands.Context, *args):
    voice_state = ctx.author.voice
    serverid = ctx.guild.id
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not await uservoice_check(ctx, voice_state=voice_state):
        return
    if args is None or len(args) == 0:
        await ctx.send("Masukan judul atau link yang ingin diputar!")
        return
    if voice_client is not None and serverid not in queues:
        await ctx.send("Pindah ke mode musik, tunggu sebentar..")
        await voice_client.disconnect(force=False)
    judul = ' '.join(args)
    shorts_pattern = r"(https?://)?(www\.)?youtube\.com/shorts/"
    if re.search(shorts_pattern, judul):
        await ctx.send("❌ Jangan pake youtube short yaaa") #Ngeblokir YT SHORTS, entah kenapa error
        return
    kalo_input_judul = not not urlparse(judul).scheme
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
            data = ydl.extract_info(judul, download=True) # Mulai Download, ambil link dari extraksi data 'id' ke variabel url
            if '/shorts/' in data.get('webpage_url', ''):  # Ngeblokir YT SHORTS, entah kenapa error
                await ctx.send(
                    "❌ Mesin pencari menemukan link YTShort yang tidak didukung. cari dengan keyword lain atau kirim link youtube")
                return
        except yt_dlp.utils.DownloadError as err:
            await notify_error(ctx, err)
            return
        if 'entries' in data:
            data = data['entries'][0]
    queue = queues.get(serverid, {}).get('queue', [])
    if len(queue) >= 1:
        await ctx.send(f'Masuk antrian! {data["title"]}. Durasi {durasi_fix(data["duration"])}. ')
    path = f'./dl/{serverid}/{data["id"]}.mp4'
    try:
        queues[serverid]['queue'].append((path, data))
    except KeyError:  # queue pertama
        queues[serverid] = {'queue': [(path, data)], 'loop': False}
        try: connection = await voice_state.channel.connect()
        except discord.ClientException:
            connection = get_voice_client_from_channel_id(voice_state.channel.id)
        connection.play(discord.FFmpegOpusAudio(path),
                        after=lambda error2=None, server_id=serverid:
                        after_track(error2, connection, server_id, ctx))
        await send_now_playing_embed(ctx, data)

@bot.command(name='radio', aliases=['r'])
async def radio(ctx: commands.Context):
    serverid = ctx.guild.id
    voice_state = ctx.author.voice
    radio_url = "https://stream.laut.fm/animefm"
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not await uservoice_check(ctx, voice_state=voice_state): return
    if serverid in queues:
        try:
            await ctx.send("Pindah ke Radio, tunggu sebentar...")
            await voice_client.disconnect(force=False)
            for path, _ in queues[serverid]['queue']:  # Stop dan hapus semua file
                try:
                    os.remove(path)
                except FileNotFoundError: pass
        except KeyError: pass
    try:
        connection = await voice_state.channel.connect()
        await ctx.send("📻️ Radio dimainkan")
        connection.play(discord.FFmpegOpusAudio(radio_url))
    except discord.ClientException:
        await voice_client.disconnect(force=False)
        await ctx.send("⏹️ Keluar dari radio.")
        return


@bot.command(name='skip', aliases=['s'])
async def skip(ctx: commands.Context, *args):
    serverid = ctx.guild.id
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    voice_state = ctx.author.voice
    if not await uservoice_check(ctx, voice_state=voice_state):
        return
    if voice_client is None and serverid not in queues:
        await ctx.send("Tidak ada yang sedang diputar.. 😕") #karena lagi ga play apa apa
        return
    elif voice_client is not None and serverid not in queues:
        await ctx.send(f"Jalankan \"{PREFIX}radio\" untuk hentikan radio") #karena ada radio
        return

    if args and args[0].lower() == 'all': # .skip all
        try:
            for path, _ in queues[serverid]['queue']: # Stop dan hapus semua file
                try: os.remove(path)
                except FileNotFoundError: pass
        except KeyError:
            pass

        queues.pop(serverid, None)
        await voice_client.disconnect(force=False)
        await ctx.send("⏹️ Skip semua antrian.")
        return
    queue = queues.get(serverid, {}).get('queue', []) # .skip biasa
    if len(queue) <= 1: # Cuma ada 1 lagu atau kosong
        voice_client.stop()
        await ctx.send("⏹️ Skip lagu, tidak ada antrian lagi.")
    else:
        await ctx.send("⏭️ Skip lagu, lanjut ke antrian berikut.")
        voice_client.stop()

@bot.command(name='loop', aliases=['l'])
async def loop(ctx: commands.Context):
    if not await uservoice_check(ctx):
        return
    try:
        loop1 = queues[ctx.guild.id]['loop']
    except KeyError:
        await ctx.send('Aku lagi ga pasang lagu apapun 😕')
        return
    queues[ctx.guild.id]['loop'] = not loop1
    await ctx.send('Looping ' + ('dinyalakan' if not loop1 else 'dimatikan'))

def get_voice_client_from_channel_id(channel_id: int):
    for voice_client in bot.voice_clients:
        if voice_client.channel == channel_id:
            return voice_client

@bot.command(name='help', aliases=['h'])
async def help1(ctx: commands.Context):
    embed = discord.Embed(
        color=discord.Color.green(),
        title='Quick Guide Chilling Amano:')
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.add_field(name=f"{PREFIX}play / p <youtube.links atau cari>",value="Memutar atau memasukan antrian lagu", inline= False)
    embed.add_field(name=f"{PREFIX}skip / s (all)", value="Skip ke lagu selanjutnya / menghapus semua antrian", inline= False)
    embed.add_field(name=f"{PREFIX}radio / r", value="Toggle untuk memainkan radio J-POP secara random", inline= False)
    embed.add_field(name=f"{PREFIX}loop / l", value="Putar lagu yang sedang diputar terus menerus", inline= False)
    embed.add_field(name=f"{PREFIX}help / h", value="Memunculkan quick help guide commands ini", inline= False)
    await ctx.send(embed=embed)

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
"""BOT DIBUAT OLEH LuthfiMC269:) check me out di https://github.com/LuthfiMC269/Chilling-Amano"""

if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemError as error:
        if True:
            raise
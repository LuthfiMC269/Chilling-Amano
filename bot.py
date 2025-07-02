#import requirements
import asyncio
import requests
import re
import sys
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import yt_dlp

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') #Masukin Token BOT DISCORD DISINI
PREFIX = os.getenv('BOT_PREFIX', '.') #Prefix manggil bot di Discord default titik (.)

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents(voice_states=True, guilds=True, guild_messages=True, message_content=True))
#define bot dc
queues = {} #antrian playlist

def main():
    if TOKEN is None:
        return ("no token provided. Please create a .example env file containing the token.\n"
                "for more information view the README.md")
    try: bot.run(TOKEN)
    except discord.PrivilegedIntentsRequired as error:
        return error

@bot.command(name='play', aliases=['p'])
async def play(ctx: commands.Context, *args):
    voice_state = ctx.author.voice
    if not await sense_checks(ctx, voice_state=voice_state):
        return

    judul = ' '.join(args)
    serverid = ctx.guild.id
    await ctx.send(f'mencari judul `{judul}`...')
    with yt_dlp.YoutubeDL({'format': 'bestaudio',
                           'source_address': '0.0.0.0',
                           'default_search': 'ytsearch',
                           'outtmpl': '%(id)s.mp4',
                           'noplaylist': True,
                           'allow_playlist_files': False,
                           'write-thumbnail': True,
                           'embed-thumbnail': True,
                           'paths': {'home': f'./dl/{serverid}'}}) as ydl:
        try:
            data = ydl.extract_info(judul, download=False)
        except yt_dlp.utils.DownloadError as err:
            return
        if 'entries' in data:
            data = data['entries'][0]

    try:
        ydl.download([judul])
        response =requests.get(data['thumbnail'])
        if response.status_code == 200:
            with open(f"./dl/{serverid}/{data["id"]}.webp", 'wb') as f:
                f.write(response.content)
                pict = discord.File(f"./dl/{serverid}/{data["id"]}.webp")
                await ctx.send(f'> Memproses Judul: {data["title"]}, Durasi {durasi_fix(data["duration"])} \n')
    except yt_dlp.utils.DownloadError as err:
        await notify_about_failure(ctx, err)
        return
    path = f'./dl/{serverid}/{data["id"]}.mp4'
    try:
        queues[serverid]['queue'].append((path, data))
    except KeyError:  # first in queue
        queues[serverid] = {'queue': [(path, data)], 'loop': False}
        try: connection = await voice_state.channel.connect()
        except discord.ClientException:
            connection = get_voice_client_from_channel_id(voice_state.channel.id)
        connection.play(discord.FFmpegOpusAudio(path),
                        after=lambda error=None, server_id=serverid:
                        after_track(error, connection, server_id))



@bot.command('loop', aliases=['l'])
async def loop(ctx: commands.Context, *args):
    if not await sense_checks(ctx):
        return
    try:
        loop = queues[ctx.guild.id]['loop']
    except KeyError:
        await ctx.send('the bot isn\'t playing anything')
        return
    queues[ctx.guild.id]['loop'] = not loop

    await ctx.send('looping is now ' + ('on' if not loop else 'off'))

def get_voice_client_from_channel_id(channel_id: int):
    for voice_client in bot.voice_clients:
        if voice_client.channel.id == channel_id:
            return voice_client

def after_track(error, connection, serverid):
    if error is not None:
        print(error)
    try:
        last_video_path = queues[serverid]['queue'][0][0]
        if not queues[serverid]['loop']:
            os.remove(last_video_path)
            queues[serverid]['queue'].pop(0)
    except KeyError: return # probably got disconnected
    if last_video_path not in [i[0] for i in queues[serverid]['queue']]: # check that the same video isn't queued multiple times
        try: os.remove(last_video_path)
        except FileNotFoundError: pass
    try:
        connection.play(discord.FFmpegOpusAudio(queues[serverid]['queue'][0][0]),
                        after=lambda error=None, server_id=serverid:
                        after_track(error, connection, server_id))
    except IndexError: # that was the last item in queue
        queues.pop(serverid) # directory will be deleted on disconnect
        asyncio.run_coroutine_threadsafe(safe_disconnect(connection), bot.loop).result()


async def safe_disconnect(connection):
    if not connection.is_playing():
        await connection.disconnect()

async def sense_checks(ctx: commands.Context, voice_state=None) -> bool: #cek apa user ada di voice channel?
    if voice_state is None: voice_state = ctx.author.voice
    if voice_state is None:
        await ctx.send('you have to be in a voice channel to use this command')
        return False

    if bot.user.id not in [member.id for member in ctx.author.voice.channel.members] and ctx.guild.id in queues.keys():
        await ctx.send('you have to be in the same voice channel as the bot to use this command')
        return False
    return True


def durasi_fix(s):
    detik = s % 3600
    menit = detik // 60
    detik = detik % 60
    return "%02d:%02d" % (menit, detik)



@bot.event
async def on_ready():
    print(f'logged in successfully as {bot.user.name}')

async def notify_about_failure(ctx: commands.Context, err: yt_dlp.utils.DownloadError):
    if True:
        # remove shell colors for discord message
        sanitized = re.compile(r'\x1b[^m]*m').sub('', err.msg).strip()
        if sanitized[0:5].lower() == "error":
            # if message starts with error, strip it to avoid being redundant
            sanitized = sanitized[5:].strip(" :")
        await ctx.send('failed to download due to error: {}'.format(sanitized))
    else:
        await ctx.send('sorry, failed to download this video')
    return



if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemError as error:
        if True:
            raise

#import requirements
import asyncio
import os
import re
import sys
from urllib.parse import urlparse
import yt_dlp
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

"""ENV LOAD"""
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN') #Masukin Token BOT DISCORD DISINI
PREFIX = os.getenv('BOT_PREFIX', '.') #Prefix manggil bot di Discord default titik (.)
BOT_REPORT_DL_ERROR = os.getenv('BOT_REPORT_DL_ERROR', '0').lower() in ('true', 't', '1')
"""END ENV LOAD"""
intents=discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX,  intents = intents) #define bot dc
bot.remove_command('help')
queues = {} #antrian playlist
guildid = 1393141345455046746
"""STARTUP"""

def main():
    if TOKEN is None:
        return "tidak ada token terdeteksi. buat file copy .example env > .env dan masukkan token bot discord kamu"
    try:
        bot.run(TOKEN)
    except discord.PrivilegedIntentsRequired as error1:
        return error1

@bot.event
async def on_ready():
    test_guild = discord.Object(id=guildid)
    nama = await bot.fetch_guild(guildid)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'{PREFIX}play 🎵'))
    try:
        synced = await bot.tree.sync(guild=test_guild)
        print(f"synced{len(synced)}")
    except Exception as e:
        print(f"error sync command: {e}")
    print(f'berhasil login dengan nama bot: {bot.user.name}, nama test guild: {nama}')

"""COMMAND BOT START DISINI"""

@bot.tree.command(name="test", description="Mengirim pesan test dari bot", guild=discord.Object(id=guildid))
async def test_command(interaction: discord.Interaction):
    await interaction.response.send_message("Halo! Ini respons dari slash command test.")
"""BOT DIBUAT OLEH LuthfiMC269:) check me out di https://github.com/LuthfiMC269/Chilling-Amano"""

if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemError as error:
        if True:
            raise
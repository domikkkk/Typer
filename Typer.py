from Common import TOKEN2
from discord.ext import commands
from discord import app_commands
import discord
import json
from Operation_on_guild import Bets, search_mess


GUILD = "ŚWIAT BUKMACHERKI"

intents = discord.Intents().default().all()

Typer = commands.Bot(command_prefix='>', intents=intents)
banned_channels = [1130195009401004042]
allowed_categories = [1128404226645692416]
Bet: Bets = None


@Typer.event
async def on_ready():
    synced = await Typer.tree.sync()
    print(len(synced))
    guilds = Typer.guilds
    guild = next((g for g in guilds if g.name == GUILD), None)
    global Bet
    Bet = Bets(guild)
    await Bet._synchronized_data(allowed_categories, banned_channels)
    Bet._delete_duplicate()
    print("Done")


@Typer.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    global Bet
    if before.author.id == Typer.user.id:
        return
    print("Edited")
    if before.content != after.content and after.channel.id not in banned_channels and after.channel.category_id in allowed_categories:
        await Bet.add_mes(after)
        Bet._delete_duplicate()


@Typer.event
async def on_message(mes: discord.Message):
    global Bet
    if mes.author.id == Typer.user.id:
        return


@Typer.event
async def on_message_delete(mes: discord.Message):
    if mes.channel.id in banned_channels or mes.channel.category_id not in allowed_categories:
        return
    # await mes.channel.send("Nie ładnie usuwać stąd wiadomość: {}".format(mes.author.mention))


@Typer.event
async def on_reaction_add(reacion: discord.Reaction, user: discord.Member):
    if user.bot:
        return
    if reacion.message.author.id == user.id and reacion.message.channel.id not in banned_channels and reacion.message.channel.category_id in allowed_categories:
        await Bet.add_mes(reacion.message)
        Bet._delete_duplicate()


@Typer.tree.command()
async def emoji(interaction: discord.Interaction):
    global Bet
    try:
        emojis_str = "Dla sukcesu" + " ".join(str(emoji) for emoji in Bet.success[:-2])
        emojis_str += '\nDla porażki' + ' '.join(str(emoji) for emoji in Bet.failure)
        await interaction.response.send_message(emojis_str)
    except Exception as e:
        await interaction.response.send_message(e, ephemeral=True)

@Typer.tree.command()
async def synchronized(interaction: discord.Interaction):
    global Bet
    try:
        Bet.bets = {}
        await interaction.response.send_message("Aktualizuję")
        res = await Bet._synchronized_data(allowed_categories, banned_channels)
        Bet._delete_duplicate()
        await interaction.channel.send(res)
    except Exception as e:
        await interaction.response.send_message(e, ephemeral=True)


@Typer.tree.command()
@app_commands.describe(name = "Nazwa członka")
async def info(interaction: discord.Interaction, name: str=None):
    global Bet
    try:
        data = Bet.ret_accuracy(name)
    except Exception:
        data = Bet.ret_accuracy()
    result = '```json\n' + json.dumps(data, indent=4, ensure_ascii=False) + '\n```'
    await interaction.response.send_message(result)


Typer.run(TOKEN)

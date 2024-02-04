from Common import TOKEN
from discord.ext import commands
from discord import app_commands
import discord
import json
import asyncio
from datetime import datetime
from Operation_on_guild import Bets
from startup import Typer, start, write_to_db, check_date


Bet: Bets = None


@Typer.event
async def on_ready():
    synced = await Typer.tree.sync()
    print(len(synced))
    guilds = Typer.guilds
    guilds = start(guilds)
    global Bet
    Bet = Bets(guilds[0])
    await Bet._synchronized_data()
    Bet._delete_duplicate()
    write_to_db(Bet.path, Bet.get_normal_data())
    print("Done")
    Typer.loop.create_task(info_per_month())


@Typer.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    global Bet
    if before.author.id == Typer.user.id:
        return
    print(f"{before.author.display_name} editied message at {datetime.utcnow()} on channel {before.channel.name}")
    if before.content != after.content and after.channel.id not in Bet.banned_channels and after.channel.category_id in Bet.allowed_categories:
        await Bet.add_mes(after)
        Bet._delete_duplicate()


@Typer.event
async def on_message(mes: discord.Message):
    global Bet
    if mes.author.id == Typer.user.id:
        return


@Typer.event
async def on_message_delete(mes: discord.Message):
    global Bet
    if mes.channel.id in Bet.banned_channels or mes.channel.category_id not in Bet.allowed_categories:
        return
    # await mes.channel.send("Nie ładnie usuwać stąd wiadomość: {}".format(mes.author.mention))
    return


@Typer.event
async def on_reaction_add(reacion: discord.Reaction, user: discord.Member):
    global Bet
    if user.bot:
        return
    if reacion.message.author.id == user.id and reacion.message.channel.id not in Bet.banned_channels and reacion.message.channel.category_id in Bet.allowed_categories:
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
@app_commands.describe(date = "Opcjonalnie miesiąc od jakiego momentu zaktualizować dane.\
    Domyślnie aktualizuje ostatni miesiąc. Format YYYY-MM. Jeśli chcemy całą historię to wpisać 'all'",
                       channel_id = "Opcjonalnie id kanału, który chcemy zaktualizować. Domyślnie wszystkie kanały typerów")
async def synchronize(interaction: discord.Interaction, date: str=None, channel_id: str=None):
    global Bet
    if not check_date(date):
        await interaction.channel.send("Podaj w formacie YYYY-MM")
        return
    try:
        channel_id = int(channel_id)
        await interaction.response.send_message("Aktualizuję...")
        res = await Bet._synchronized_data(date, channel_id)
        Bet._delete_duplicate()
        write_to_db(Bet.path, Bet.get_normal_data())
        await interaction.channel.send(res)
    except Exception as e:
        await interaction.response.send_message(e, ephemeral=True)


@Typer.tree.command()
@app_commands.describe(name = "Nazwa członka. Domyślnie wszyscy",
                       date = "Miesiąc, z którego chcemy statystyki.\
                           Domyślnie ostatni miesiąc. Format YYYY-MM. Jeśli chcemy całą historię to wpisać 'all'.")
async def info(interaction: discord.Interaction, name: str=None, date: str=None):
    global Bet
    if not check_date(date):
        await interaction.channel.send("Podaj w formacie YYYY-MM")
        return
    data = await Bet.ret_accuracy(name, date)
    await interaction.response.send_message("...")
    for name in data:
        data_to_show = {name: data[name]}
        result = '```json\n' + json.dumps(data_to_show, indent=4, ensure_ascii=False) + '\n```'
        await interaction.channel.send(result)


async def info_per_month():
    await Typer.wait_until_ready()
    global Bet
    channel_id = 1158130114933047387
    channel_id = 1114293456127414293
    channel = Typer.get_channel(channel_id)
    while not Typer.is_closed():
        day = datetime.utcnow().day
        print(day)
        if day == 1:
            print("Comiesięczne info")
            data = await Bet.ret_accuracy()
            for name in data:
                data_to_show = {name: data[name]}
                result = '```json\n' + json.dumps(data_to_show, indent=4, ensure_ascii=False) + '\n```'
                await channel.send(result)
            write_to_db(Bet.path, Bet.get_normal_data())
        await asyncio.sleep(24 * 60 * 60)


Typer.run(TOKEN)

import json
from typing import Sequence
import discord
from discord.ext import commands


WRITE = 0
READ = 1


intents = discord.Intents().default().all()
Typer = commands.Bot(command_prefix='>', intents=intents)


def read_from_db(filename: str):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data


def write_to_db(filename: str, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)


def guilds(typ, *, data: dict=None):
    if typ == READ:
        guilds = read_from_db("config.json")
        return guilds
    if typ == WRITE:
        if not data:
            raise ValueError
        del data["guild"]
        write_to_db("config.json", data)


def start(guild: Sequence[discord.Guild]):
    all_guilds = guilds(READ)
    for g in all_guilds:
        g["guild"] = next((gg for gg in guild if gg.name == g['name']), None)
        if g["guild"]:
            print(f"Found {g['name']}") 
    return all_guilds
    
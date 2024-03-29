import discord
import numpy as np
from datetime import datetime
from startup import read_from_db


class Bets:
    def __init__(self, guild: dict) -> None:
        self._guild: discord.Guild = guild['guild']
        self.allowed_categories = guild["allowed_cat"]
        self.banned_channels = guild["banned_ch"]
        self.path = guild["path"]
        self.members_id: dict[int|discord.User] = {}
        for member in self._guild.members:
            self.members_id[member.id] = member
        self.bets = {}
        try:
            data = read_from_db(self.path)
            for str_id in data:
                self.bets[int(str_id)] = data[str_id]
        except Exception as e:
            print(e)
        self.success = ['✅', str(discord.utils.get(self._guild.emojis, name='success')), '<:7425classiccheckmark:', '<:zielony:']
        self.failure = ['⛔️', str(discord.utils.get(self._guild.emojis, name='x_')), '❌']

    async def add_mes(self, mes: discord.Message):
        author_id = mes.author.id
        date = get_year_month(mes.created_at)
        if author_id not in self.bets:
            self.bets[author_id] = {date: {"0": [], "1": []}}
        elif date not in self.bets[author_id]:
            self.bets[author_id][date] = {"0": [], "1": []}
        await self.analize_mes(mes, date)
        
    async def analize_mes(self, mes: discord.Message, date):
        author_id = mes.author.id
        if any(succ in mes.content for succ in self.success):
            self.bets[author_id][date]["1"].append(mes.id)
            return
        elif any(fail in mes.content for fail in self.failure):
            self.bets[author_id][date]["0"].append(mes.id)
            return
        for reaction in mes.reactions:
            a = 0
            async for user in reaction.users():
                if user.id == author_id:
                    a = 1
            if a == 0:
                continue
            if str(reaction.emoji) in self.success:
                self.bets[author_id][date]["1"].append(mes.id)
                break
            elif str(reaction.emoji) in self.failure:
                self.bets[author_id][date]["0"].append(mes.id)
                break
        return
                
    async def ret_accuracy(self, au:str=None, date:str=None):
        data = {}
        for id in self.bets:
            data[self.members_id[id].display_name] = {month: {"Średnia": self._entropy(id, month),
                                                                "Ilość zakładów": self._get_games(id, month)}
                                                        for month in self.bets[id]}
        date = self.filtr_date(date)
        if date is not None:
            for name in data:
                if date in data[name]:
                    data[name] = {date: data[name][date]}
                else:
                    data[name] = {date: "Brak danych z tego miesiąca"}
        if au is not None:
            au = au.lower()
            for name in data:
                if podciag(au, name) / max(len(au), len(name)) > 0.7:
                    return {name: data[name]}
            return {"message": f"Brak info na temat członka {au}"}
        return data

    def _entropy(self, id, date:str):
        try:
            return round(100* len(self.bets[id][date]["1"]) / self._get_games(id, date), 2)
        except ZeroDivisionError:
            return 0.0

    def _get_games(self, id, date):
        return len(self.bets[id][date]["0"]) + len(self.bets[id][date]["1"])

    def _delete_duplicate(self):
        for id in self.bets:
            for month in self.bets[id]:
                self.bets[id][month]["0"] = list(set(self.bets[id][month]["0"]))
                self.bets[id][month]["1"] = list(set(self.bets[id][month]["1"]))
            self.bets[id] = {month: value for month, value in self.bets[id].items() if (len(value['0']) != 0 or len(value['1']) != 0)}

    async def _synchronized_data(self, date=None, chan_id=None):
        if chan_id is not None:
            channel = self._guild.get_channel(chan_id)
            if chan_id not in self.banned_channels and channel.category_id in self.allowed_categories:
                print(channel.category.name)
                print('\t' + channel.name)
                await self.analize_history(channel, date)
                return "Pomyślnie zaktualizowano"
            return "Ten kanał nie jest analizowany"
        for category in self._guild.categories:
            print(category.name)
            if category.id in self.allowed_categories:
                for channel in category.channels:
                    if channel.id in self.banned_channels:
                        continue
                    print('\t' + channel.name)
                    await self.analize_history(channel, date)
        return "Pomyślnie zaktualizowano"

    async def analize_history(self, channel: discord.TextChannel, date: str=None):
        date = self.filtr_date(date)
        if date is not None:
            date = get_datetime_from_year_month(date)
        async for message in channel.history(limit=None, oldest_first=True, after=date):
            if message.author.bot:
                continue
            await self.add_mes(message)

    def get_normal_data(self):
        data = {}
        for id in self.bets:
            data[id] = self.bets[id]
        return data

    def filtr_date(self, date: str=None):
        if not date:
            date = get_year_month(datetime.utcnow())
        elif date == "all":
            date = None
        else:
            date = '-'.join([str(int(x)) for x in date.split('-')])
        return date


async def search_mess(id, interaction: discord.Interaction):
    async for message in interaction.channel.history(limit=None, oldest_first=True):
        if message.id == id:
            return message.content


def get_year_month(date: datetime):
    return str(date.year) + '-' + str(date.month)


def get_datetime_from_year_month(date):
    [year, month] = date.split('-')
    year = int(year)
    month = int(month)
    date = datetime(year, month, day=1)
    return date


def podciag(s1: str, s2: str):
    s1 = s1.lower()
    s2 = s2.lower()
    m = len(s1)
    n = len(s2)
    L = np.zeros((m+1, n+1))
    for i in range(m):
        for j in range(n):
            if s1[i] == s2[j]:
                L[i+1, j+1] = 1 + L[i, j]
            else:
                L[i+1, j+1] = max(L[i+1, j], L[i, j+1])
    return L[m, n]

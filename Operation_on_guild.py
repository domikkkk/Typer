import discord


class Bets:
    def __init__(self, guild: discord.Guild) -> None:
        self._guild = guild
        self._members = guild.members
        self.members_id = {}
        for member in self._members:
            self.members_id[member.id] = member
        self.bets = {}
        self.success = ['✅', str(discord.utils.get(guild.emojis, name='success')), '<:7425classiccheckmark:', '<:zielony:']
        self.failure = ['⛔️', str(discord.utils.get(guild.emojis, name='x_')), '❌']

    async def add_mes(self, mes: discord.Message):
        author = mes.author.nick if mes.author.nick is not None else mes.author.global_name
        if not author:
            author = mes.author.name
        if author not in self.bets:
            self.bets[author] = {0: [], 1: []}
        await self.analize_mes(mes)
        
    async def analize_mes(self, mes: discord.Message):
        name = mes.author.nick if mes.author.nick is not None else mes.author.global_name
        if not name:
            name = mes.author.name
        if any(succ in mes.content for succ in self.success):
            self.bets[name][1].append(mes.id)
            return
        elif any(fail in mes.content for fail in self.failure):
            self.bets[name][0].append(mes.id)
            return
        for reaction in mes.reactions:
            a = 0
            async for user in reaction.users():
                if user.id == mes.author.id:
                    a = 1
            if a == 0:
                return
            if str(reaction.emoji) in self.success:
                self.bets[name][1].append(mes.id)
            elif str(reaction.emoji) in self.failure:
                self.bets[name][0].append(mes.id)
        return
                

    def ret_accuracy(self, au:str=None):
        if not au:
            return {member: {"Średnia": self._entropy(member), "Ilość zakładów": self._get_games(member)} for member in self.bets}
        au = au.lower()
        for member in self.bets:
            indexes = find_KMP(au, member.lower())
            if len(indexes) > 0 and len(au)/len(member) > 0.6:
                au = member
                break
        return {au: {"Średnia": self._entropy(au), "Ilość zakładów": self._get_games(au)}}

    def _entropy(self, member):
        try:
            return round(100* len(self.bets[member][1]) / self._get_games(member), 1)
        except ZeroDivisionError:
            return 0.0

    def _get_games(self, member):
        return len(self.bets[member][1]) + len(self.bets[member][0])

    def _delete_duplicate(self):
        for member in self.bets:
            self.bets[member][0] = list(set(self.bets[member][0]))
            self.bets[member][1] = list(set(self.bets[member][1]))

    async def _synchronized_data(self, allowed_categories, banned_channels):
        res = ''
        for category in self._guild.categories:
            print(category.name)
            if category.id in allowed_categories:
                for channel in category.channels:
                    if channel.id in banned_channels:
                        continue
                    print('\t' + channel.name)
                    res += channel.name + '\n'
                    await self.analize_history(channel)
        return res + 'Done'

    async def analize_history(self, channel: discord.TextChannel):
        async for message in channel.history(limit=None, oldest_first=True):
            if message.author.bot:
                continue
            await self.add_mes(message)


async def search_mess(id, interaction: discord.Interaction):
    async for message in interaction.channel.history(limit=None, oldest_first=True):
        if message.id == id:
            return message.content


def find_KMP(string, text):
    lista = []
    if len(text) - len(string) < 0 or len(string) == 0:
        return lista
    m = len(string) #dlugosc wzorca
    n = len(text)   #dlugosc tekstu
    i, j = 0, 0     #indeks tekstu, wzorca
    prefix_arr = prefix(string)
    while i != n:
        # print(i, j)
        if text[i] == string[j]:
            i += 1
            j += 1
        if j == m:
            lista.append(i - j)
            j = prefix_arr[j-1]
        elif i < n and string[j] != text[i]:
            if j== 0:
                i+=1
            else:
                j = prefix_arr[j-1]
    return lista


def prefix(pattern):
    m = len(pattern)  # dlugosc wzorca
    prefix_arr = [0]*m  # tablica z m zer
    i, j = 0, 1  # indeksy
    while j != m:
        if pattern[j] == pattern[i]:
            i += 1
            prefix_arr[j] = i
            j += 1
        elif i != 0:
            i = prefix_arr[i-1]
        else:
            prefix_arr[j] = 0
            j += 1
    return prefix_arr

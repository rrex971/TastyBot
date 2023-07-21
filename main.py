from calc_pp import pp, init_api
from twitchio.ext import commands, routines
from db_loader import load_db
from osu import Mods
import discord
import requests as r
from discord.ext import commands as dcommands
import random
import os,sys
import subprocess as sp
import argparse
import asyncio
try:
    os.chdir('recbot/')
except Exception as e:
    pass
parser = argparse.ArgumentParser(prog='plink',description='plonk',epilog='pleep', exit_on_error=False)
parser.add_argument('-mods', '-m')
parser.add_argument('-ppmin', '-min', type=int)
parser.add_argument('-ppmax', '-max', type=int)
parser.add_argument('-bpm', type=int)
parser.add_argument('-pu', '-playsunder', type=int)
parser.add_argument('-ar','-approachrate', type=float)
parser.add_argument('-minl', '-minlength', type=int)
parser.add_argument('-maxl', '-maxlength', type=int)

api = init_api()
dbot = dcommands.Bot(command_prefix='!', intents=discord.Intents.default())

c, db = load_db()
invmodValues = {0:'NM', 8:'HD', 16:'HR', 64:'DT', 576:'NC', 1024: "FL", 2: "EZ", 256: "HT"}
modValues = {"NM":0, "HD":8, "HR":16, "DT":64, "NC":576, "FL":1024, "EZ":2, "HT":256}
config = open("config.txt")
configlist = config.readlines()
configdict = {}

onlineAccess = ['rrex972']

for i in configlist:
    configdict[i.split(":",maxsplit=1)[0].strip()] = i.split(":",maxsplit=1)[1].strip()

bot = commands.Bot(token=configdict["oauth"],
    client_id=configdict["client_id"],
    nick=configdict["bot_name"],
    prefix=configdict["prefix"],
    initial_channels=['rrex972', 'btmc', 'getchanned', 'znxtech'], heartbeat=15) 


@bot.event()
async def event_ready():
    print('Logged in')

@bot.event()
async def event_channel_join(channel):
    print(f'Joined channel {channel.name}')

@bot.event()
async def event_reconnect():
    print(f'Reconnecting...')

@routines.routine(seconds=5.0)
async def check_live():
    await bot.wait_for_ready()
    for i in bot.connected_channels:
        user = await i.user()
        print("Checking: ", user.name)
        res = await bot.search_channels(query=user.name)
        if res[0].live and user.name not in onlineAccess:
            await bot.part_channels([user.name])
            print(user)
            print(f'Parted channel {user.name} due to being live.')     

@commands.cooldown(rate=1, per=0.1, bucket=commands.Bucket.channel)


@bot.command(name="battery")
async def battery(ctx):

    cap = open('/sys/class/power_supply/battery/capacity')

    charging = open('/sys/class/power_supply/battery/status')
    await send(ctx, f"Server phone battery: {cap.read()}% ({charging.read()})")

@bot.command(name="rec", aliases=["recommend", 'REC'])
async def rec(ctx, *args):
    parsed = parser.parse_known_args(args)[0]
    mods = parsed.mods
    acc = get_user_osu(ctx.author.id)
    if acc == None:
        await send(ctx, f"{ctx.author.mention} No account linked, please link your account with <link [username]")
        return
    else:
        acc = acc[0]
    ppmin = parsed.ppmin
    ppmax = parsed.ppmax
    userbestscores = api.get_user_scores(user=acc, type='best', mode='osu', limit=10)
    if ppmin == None:
        ppmin = userbestscores[-1].pp
    if ppmax == None:
        ppmax = userbestscores[0].pp
    print(parsed)
    if mods != None:
        mods=mods.upper()
        modparse = [mods[i:i+2].upper() for i in range(0, len(mods), 2)]
        modsEnum = 0
        for i in modparse:
            if i in modValues.keys():   
                modsEnum += modValues[i]
            else:
                await send(ctx, "Invalid mod combination, please try again.")
                return
        modsF = f" enabled_mods = {modsEnum} and"
    else:
        mods = "NM"
        modsF = ''
        modsEnum = 0
    add = not all(value is None for value in [parsed.bpm, parsed.ar, parsed.pu, parsed.minl, parsed.maxl])
    lim = 50
    while True:
        c.execute(f"select beatmap_id, maxcombo, score_id from osu_scores_high where{modsF} pp between {ppmin} and {ppmax} and rank in ('S', 'SH', 'X', 'XH') order by RANDOM() limit {lim};")
        mapList = c.fetchall()
        unsortedmapObjs = api.get_beatmaps([x[0] for x in mapList])
        mapObjs = sorted(unsortedmapObjs, key=lambda map: [x[0] for x in mapList].index(map.id))
        if add:
            checkBPM = parsed.bpm is not None
            checkAR = parsed.ar is not None
            checkPU = parsed.pu is not None
            checkMin = parsed.minl is not None
            checkMax = parsed.maxl is not None
            map = None
            rmap = None
            for i, map in enumerate(mapObjs):
                idx = i
                rmap = mapList[i]
                print(i, map, rmap)
                if checkBPM and map.bpm != parsed.bpm:
                    continue
                if checkAR and map.ar != parsed.ar:
                    continue
                if checkPU and map.beatmapset.play_count >= parsed.pu:
                    continue
                if checkMin and map.total_length < parsed.minl:
                    continue
                if checkMax and map.total_length > parsed.maxl:
                    continue
                if not (map.max_combo - int(rmap[1])) < 50:
                    c.execute(f"DELETE FROM osu_scores_high WHERE score_id = {rmap[2]}")
                    print(f"Deleted {rmap[2]}")
                    continue
                else:
                    print(map.max_combo - int(rmap[1]))
                    break
            if idx != 49:
                mapID = map.id
                break
        else:
            for i, map in enumerate(mapObjs):
                rmap = mapList[i]
                mapID = map.id
                if ((map.max_combo - int(rmap[1])) < 50):
                    print(map.max_combo - int(rmap[1]))
                    break
                else:
                    c.execute(f'delete from osu_scores_high where score_id = {rmap[2]}')
                    print(f'Deleted {rmap[2]}')
                    continue
            break
    map_atttributes = api.get_beatmap_attributes(mapID, mods=Mods(modsEnum), ruleset='osu')
    await send(ctx, f"{ctx.author.mention} https://osu.ppy.sh/b/"+str(mapID)+ " | "+map.beatmapset.artist+" - "+map.beatmapset.title+" ["+map.version+"], ("+map.beatmapset.creator+", "+str(round(map_atttributes.star_rating, 2))+"*) +"+mods+" | BPM: "+str(map.bpm)+" | 100%: "+str(round(pp(map, map_atttributes, modsEnum, 1), 2)))
    #await asyncio.sleep(2)
    #await ctx.send("https://osu.ppy.sh/b/"+str(mapID))


@bot.command(name = "dm")
async def dm(ctx, *messageL):
    message = " ".join(messageL)
    user = await dbot.fetch_user(263270117708791809)
    await user.send(f"""Message from {ctx.author.name}: {message}""")
    await send(ctx, f"{ctx.author.mention} successfully sent your dm to @rrex972 DinkDonk")
    
@bot.command(name = "test")
async def test(ctx):
    await send(ctx, "PogU IT WORKS LETSGO LETSGO LETSGO LETSGO LETSGO LETSGO LETSGO LETSGO LETSGO LETSGO ")
    
@bot.command(name = "meow")
async def meow(ctx):
    await send(ctx, "meow")

@bot.command(name = "plink")
async def meow(ctx):
    await send(ctx, "plink")

@bot.command(name = "kill")
async def kill(ctx):
    if ctx.author.name.lower() == "rrex972":
        await send(ctx, "oh nyo bot is kil reeferSad")
        exit()
    else:
        await send(ctx, "ICANT bozo tried to kill")


@bot.command(name = "gitpull")
async def gitpull(ctx):
    if ctx.author.name.lower() == "rrex972":
        await send(ctx, "Pulling latest changes from GitHub and restarting.")
        zip = r.get('https://github.com/rrex971/TastyBot/archive/refs/heads/main.zip')
        os.chdir('..')
        open('recbot.zip', 'wb').write(zip.content)
        await bot.close()
        await dbot.close()
        try:
            sp.call(['sh', '/storage/self/primary/recbot/pull.sh'])
        except:
            print("On Windows, no shell script") 
        try:
            os.execv(sys.executable, [sys.executable, os.path.abspath(__file__)])
        except Exception as e:
            print(e)
    else:
        await send(ctx, "erm you cant use this Awkward")

@bot.command(name='link')
async def link(ctx, *usernameL):
    username = " ".join(usernameL)
    authID = ctx.author.id
    c.execute(f'select userID from users where userID = {authID}')
    searchres = c.fetchall()
    if searchres == []:
        user = api.get_user(user=username)
        osuid = user.id
        c.execute(f"insert into users values(?, ?);", (authID, osuid))
        db.commit()
        await send(ctx, f"Successfully linked osu! profile {user.username} to {ctx.author.mention} .")
    else:
        await send(ctx, "Your account is already linked.")

@bot.command(name='unlink')
async def unlink(ctx, user_name):
    if ctx.author.name == "rrex972":
        user = await bot.fetch_users(names=[user_name])
        print(user[0].id)
        c.execute(f"delete from users where userID = {user[0].id}")
        db.commit()
        await send(ctx, "Removed user from database.")
    else:
        await send(ctx, f"{ctx.author.mention}, you can't use this command Stare")
'''
@bot.command(name = 'worstbot')
async def worstbot(ctx):
    botlist = ['sheppsubot', 'PogpegaBot', 'osuWHO', 'StreamElements', 'FossaBot', '']
'''

@bot.command(name = "roll")
async def roll(ctx, num):
    rnum = random.choice(range(0,int(num)+1))
    await send(ctx, f"{ctx.author.mention} You rolled {rnum} NAILS")
    if "727" in str(rnum):
        await asyncio.sleep(2)
        await send(ctx, "WYSI THE NUMBER WYSI WHEN YOU SEE IT WYSI WHEN YOU FUCKING SEE IT WYSI THE NUMBER WYSI WHEN YOU SEE IT WYSI WHEN YOU FUCKING SEE IT WYSI THE NUMBER WYSI WHEN YOU SEE IT WYSI WHEN YOU FUCKING SEE IT WYSI THE NUMBER WYSI WHEN YOU SEE IT WYSI WHEN YOU FUCKING SEE IT WYSI THE NUMBER WYSI WHEN YOU SEE IT WYSI WHEN YOU FUCKING SEE IT WYSI ")
@bot.command(name = "commands")
async def commands(ctx, aliases = ["help"]):
    command = ""
    print(bot.commands)
    for i in bot.commands.values():
        command += f"""| {str(configdict["prefix"])+str(i.name)} """
    await send(ctx, f"Bot commands: {command}")


@bot.command(name="pasta")
async def test(ctx, *args):
    if ctx.author.name.lower() == "tastybot01".lower():
        return
    else:
        if args[0].lower() == 'search':
            with open('copypasta.txt', 'r', encoding = "UTF8") as f:
                s = 0
                res = []
                for i in f.readlines():
                    if args[1] in i:
                        res.append(i)
                        s = 1
                        break
                if s == 0:
                    await send(ctx, "no matching copypasta found meow")
                else:
                    await send(ctx, f"{random.choice(res)}")
        if args[0].lower() == 'new' or args[0].lower() == 'add':
            with open("copypasta.txt", "r+", encoding = "UTF8") as f:
                if (" ".join(args[1:])+"\n") not in f.readlines():
                    if len((" ".join(args[1:])+"\n").strip()) != 0:
                        if len((" ".join(args[1:])+"\n").strip()) >= 5:
                            f.seek(0,2)
                            f.write(" ".join(args[1:])+"\n")
                            await send(ctx, "added copypasta SoCute")
                        else:
                            await send(ctx, "Stare pasta less than 5 characters long")
                    else:
                        await send(ctx, "Stare i know what you're doing")
                else:
                    await send(ctx, "Stare pasta already added")
        if args[0].lower() == 'random':
            with open("copypasta.txt", "r", encoding="UTF8") as f:
                await send(ctx, f"{random.choice(f.readlines())}")

async def send(ctx, message: str):
    await ctx.send('/me Tasty '+message)

def get_user_osu(authorid):
    c.execute(f"select osuID from users where userID = {authorid}")
    res = c.fetchall()
    if res != []:
        return res[0]
    else:
        return None


async def run_bots():
    tasks = [dbot.start(configdict['discord_token']), bot.start()]
    await asyncio.gather(*tasks)

check_live.start()
loop = asyncio.get_event_loop()
loop.run_until_complete(run_bots())



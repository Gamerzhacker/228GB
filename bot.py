import discord
from discord.ext import commands
import docker
import json
import random
import string

token = ''
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Load admins
with open("botadmins.json", "r") as f:
    bot_admins = json.load(f)

def is_admin(user_id):
    return str(user_id) in bot_admins

def load_vps_data():
    with open("vps_data.json", "r") as f:
        return json.load(f)

def save_vps_data(data):
    with open("vps_data.json", "w") as f:
        json.dump(data, f, indent=2)

def generate_pass(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.command()
async def botinfo(ctx):
    await ctx.send("Bot Developer: VPS Bot")

@bot.command()
async def botadmin(ctx):
    await ctx.send(f"Admins: {', '.join(bot_admins)}")

@bot.command()
async def botadmin_add(ctx, userid: str):
    if is_admin(ctx.author.id):
        bot_admins.append(userid)
        with open("botadmins.json", "w") as f:
            json.dump(bot_admins, f)
        await ctx.send(f"Added {userid} as admin.")
    else:
        await ctx.send("You are not an admin.")

@bot.command()
async def deployipv4(ctx):
    user_id = str(ctx.author.id)
    client = docker.from_env()
    ssh_pass = generate_pass()

    container = client.containers.run(
        "vps_ubuntu",
        detach=True,
        ports={
            '22/tcp': None, '443/tcp': None, '80/tcp': None,
            '8080/tcp': None, '2022/tcp': None, '5080/tcp': None, '3001/tcp': None
        },
        name=f"vps_{user_id}_{random.randint(1000,9999)}"
    )

    container.reload()
    ports = container.attrs['NetworkSettings']['Ports']
    port_map = {port: ports[port][0]['HostPort'] for port in ports}

    vps_info = {
        "container_id": container.id,
        "user": "root",
        "pass": ssh_pass,
        "ports": port_map
    }

    data = load_vps_data()
    data.setdefault(user_id, []).append(vps_info)
    save_vps_data(data)

    await ctx.send(f"VPS created with ports: {port_map}\nSSH user/pass: root / {ssh_pass}")

@bot.command()
async def list(ctx):
    user_id = str(ctx.author.id)
    data = load_vps_data()
    user_vps = data.get(user_id, [])
    if not user_vps:
        await ctx.send("No VPS found.")
        return
    response = ""
    for i, vps in enumerate(user_vps, 1):
        response += f"#{i}: Ports: {vps['ports']} | user: {vps['user']} | pass: {vps['pass']}\n"
    await ctx.send(response)

@bot.command()
async def nodeadmin(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("Admin only.")
    data = load_vps_data()
    await ctx.send(json.dumps(data, indent=2))

@bot.command()
async def nodes(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("Admin only.")
    data = load_vps_data()
    response = ""
    for uid in data:
        for vps in data[uid]:
            response += f"User: {uid} | user/pass: {vps['user']} / {vps['pass']}\n"
    await ctx.send(response)

@bot.command()
async def delvps(ctx, userid: str):
    if not is_admin(ctx.author.id):
        return await ctx.send("Admin only.")
    data = load_vps_data()
    if userid in data:
        client = docker.from_env()
        for vps in data[userid]:
            try:
                cont = client.containers.get(vps["container_id"])
                cont.kill()
                cont.remove()
            except:
                pass
        del data[userid]
        save_vps_data(data)
        await ctx.send(f"Deleted all VPS for user {userid}")
    else:
        await ctx.send("No VPS found for this user.")

@bot.command()
async def ipv4(ctx, userid: str, ip: str, user: str, passwd: str):
    if not is_admin(ctx.author.id):
        return await ctx.send("Admin only.")
    data = load_vps_data()
    entry = {"ip": ip, "user": user, "pass": passwd}
    data.setdefault(userid, []).append(entry)
    save_vps_data(data)
    await ctx.send(f"Assigned manual VPS to {userid}")

@bot.command()
async def dropipv4(ctx):
    if not is_admin(ctx.author.id):
        return await ctx.send("Admin only.")
    await ctx.send("Paste drop VPS list (userid ip user pass) one per line:")

    def check(msg): return msg.author == ctx.author and msg.channel == ctx.channel
    msg = await bot.wait_for('message', check=check, timeout=120)
    lines = msg.content.strip().split("\n")

    data = load_vps_data()
    for line in lines:
        parts = line.strip().split()
        if len(parts) == 4:
            uid, ip, user, passwd = parts
            entry = {"ip": ip, "user": user, "pass": passwd}
            data.setdefault(uid, []).append(entry)
    save_vps_data(data)
    await ctx.send("Added dropped VPS list.")

# run the bot
bot.run(token)

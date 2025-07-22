import os
import json
import sys
import hmac
import hashlib
import threading
from flask import Flask, request, jsonify
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from mcrcon import MCRcon
from aiolimiter import AsyncLimiter
import pymysql

# Load environment
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SHOP_LOG_CHANNEL_ID = int(os.getenv("SHOP_LOG_CHANNEL_ID", 0))
REWARD_INTERVAL_MINUTES = int(os.getenv("REWARD_INTERVAL_MINUTES", 30))
REWARD_POINTS = int(os.getenv("REWARD_POINTS", 10))
TIP4SERV_SECRET = os.getenv("TIP4SERV_SECRET", "")
TIP4SERV_TOKEN = os.getenv("TIP4SERV_TOKEN", "")

# Parse multiple MariaDB configs from env
# Expected JSON: [{"name":"primary","host":"...","port":3306,"user":"...","password":"...","database":"..."}, ...]
DB_CONFIGS = json.loads(os.getenv("SQL_DATABASES", "[]"))
# Create connections
db_conns = {}
for cfg in DB_CONFIGS:
    db_conns[cfg["name"]] = pymysql.connect(host=cfg["host"], port=int(cfg["port"]),
                                             user=cfg["user"], password=cfg["password"],
                                             database=cfg["database"], autocommit=True)

# Rate limiter for webhooks: e.g., 5 req per second
webhook_limiter = AsyncLimiter(5, 1)

# RCON settings
RCON_SERVERS = json.loads(os.getenv("RCON_SERVERS", "[]"))

# ===== Database Helpers =====
def get_cursor(db_name="primary"):    
    return db_conns[db_name].cursor()

def get_balance(player_id, db_name="primary"):
    cur = get_cursor(db_name)
    cur.execute("SELECT COALESCE(SUM(points),0) FROM transactions WHERE player_id=%s", (player_id,))
    bal = cur.fetchone()[0]
    cur.close()
    return bal

def log_transaction(player_id, points, status, source="shop", db_name="primary"):
    cur = get_cursor(db_name)
    cur.execute(
        "INSERT INTO transactions (player_id, points, status, source) VALUES (%s,%s,%s,%s)",
        (player_id, points, status, source)
    )
    cur.close()
    return get_balance(player_id, db_name)

def queue_delivery(player_id, item_name, command, map_name, price, db_name="primary"):
    cur = get_cursor(db_name)
    cur.execute(
        "INSERT INTO pending_deliveries (player_id, item_name, command, map, price) VALUES (%s,%s,%s,%s,%s)",
        (player_id, item_name, command, map_name, price)
    )
    cur.close()

def deliver_queued_items(db_name="primary"):
    cur = get_cursor(db_name)
    cur.execute("SELECT id, player_id, command FROM pending_deliveries WHERE status='pending'")
    rows = cur.fetchall(); count = 0
    for id_, pid, cmd in rows:
        try:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                mcr.command(cmd)
            cur.execute("UPDATE pending_deliveries SET status='delivered' WHERE id=%s", (id_,))
            count += 1
        except:
            continue
    cur.close()
    return count

# ===== Flask Webhook =====
app = Flask(__name__)

@app.route('/tip4serv-webhook', methods=['POST'])
async def tip4serv_webhook():
    async with webhook_limiter:
        signature = request.headers.get('X-Tip4Serv-Signature','')
        body = request.get_data()
        if TIP4SERV_SECRET:
            mac = hmac.new(TIP4SERV_SECRET.encode(), body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(mac, signature):
                return jsonify({'error':'Invalid signature'}), 403
        data = request.json or {}
        player_id = data.get('eos_id') or data.get('player_id')
        points = int(data.get('points',0))
        log_channel = bot.get_channel(SHOP_LOG_CHANNEL_ID)
        if not player_id or points<=0:
            if log_channel: await log_channel.send(f"❌ Invalid webhook payload: {data}")
            return jsonify({'error':'Invalid data'}), 400
        # Credit
        new_bal = log_transaction(player_id, points, 'Success', source='tip4serv')
        if log_channel: await log_channel.send(f"💸 Tip4Serv: +{points} points to {player_id} (now {new_bal})")
        return jsonify({'status':'ok','balance':new_bal}), 200

# Run Flask in background
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()

# ===== Discord Bot =====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)
bot.temp_purchases = {}

# RCON env
RCON_HOSTS = RCON_SERVERS  # GUI populates this in .env
RCON_HOST = os.getenv('RCON_HOST','127.0.0.1')
RCON_PORT = int(os.getenv('RCON_PORT',25575))
RCON_PASSWORD = os.getenv('RCON_PASSWORD','changeme')

# Reward loop
@tasks.loop(minutes=REWARD_INTERVAL_MINUTES)
async def reward_active_players():
    for guild in bot.guilds:
        for member in guild.members:
            if member.bot: continue
            eos_id = get_balance.__self__(member.id)  # placeholder: implement get_eos_for_discord
            if not eos_id: continue
            bal = log_transaction(eos_id, REWARD_POINTS, 'IntervalReward')
            try:
                await send_rcon(f"chat {member.display_name} WrecksShop <RichColor Color=\\\"1,1,0,1\\\">+{REWARD_POINTS}! (total {bal})</>")
            except Exception as e:
                print(f"[RCON] reward failed: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    reward_active_players.start()

# In-game chat handlers
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.strip()
    eos_id = get_eos_for_discord(message.author.id)
    if not eos_id:
        return
    if content == MESSAGES["PointsCmd"]:
        points = get_balance(eos_id)
        try:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                mcr.command(f"chat {message.author.display_name} {MESSAGES['Sender']} " + 
                            MESSAGES["HavePoints"].format(points))
        except Exception as e:
            print(f"[RCON] /points error: {e}")
    elif content.startswith(MESSAGES["TradeCmd"]):
        parts = content.split()
        if len(parts) != 3: return
        _, target_name, amt_str = parts
        try:
            amount = int(amt_str)
        except:
            return
        if amount <= 0: return
        from_user, to_user = message.author, discord.utils.get(message.guild.members, name=target_name)
        if not to_user:
            return
        if from_user.id == to_user.id:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                mcr.command(f"chat {from_user.display_name} {MESSAGES['Sender']} " + MESSAGES['CantGivePoints'])
            return
        from_id, to_id = get_eos_for_discord(from_user.id), get_eos_for_discord(to_user.id)
        if not from_id or not to_id: return
        bal = get_balance(from_id)
        if bal < amount:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                mcr.command(f"chat {from_user.display_name} {MESSAGES['Sender']} " + MESSAGES['NoPoints'])
            return
        log_transaction(from_id, -amount, "TradeSent", source=f"to:{to_user.display_name}")
        log_transaction(to_id, amount, "TradeReceived", source=f"from:{from_user.display_name}")
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            mcr.command(f"chat {from_user.display_name} {MESSAGES['Sender']} " + 
                        MESSAGES['SentPoints'].format(amount, to_user.display_name))
            mcr.command(f"chat {to_user.display_name} {MESSAGES['Sender']} " + 
                        MESSAGES['GotPoints'].format(amount, from_user.display_name))

# Shop UI views
class ShopCategoryDropdown(Select):
    def __init__(self, category_name, items):
        options = [
            discord.SelectOption(label=i['name'], description=f"{i['price']} shop points")
            for i in items[:25]
        ]
        super().__init__(placeholder=f"🛒 {category_name}", min_values=1, max_values=1, options=options)
        self.items = items

    async def callback(self, interaction: discord.Interaction):
        item = next(i for i in self.items if i['name']==self.values[0])
        player_id = get_eos_for_discord(interaction.user.id)
        if not player_id:
            return await interaction.response.send_message("⚠️ You’re not linked.", ephemeral=True)
        await interaction.response.send_message("Select your map:", view=MapSelectView(interaction.user.id), ephemeral=True)
        interaction.client.temp_purchases[interaction.user.id] = item

class MapSelect(Select):
    def __init__(self, user_id):
        self.user_id = user_id
        maps = ["The Island","Scorched Earth","Aberration","Extinction","Genesis","Genesis Part 2","Ragnarok","Valguero","Crystal Isles","Fjordur"]
        opts = [discord.SelectOption(label=m, value=m) for m in maps]
        super().__init__(placeholder="Select map", min_values=1, max_values=1, options=opts)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id!=self.user_id:
            return await interaction.response.send_message("❌ Not your session.", ephemeral=True)
        purchase = interaction.client.temp_purchases.pop(self.user_id, None)
        if not purchase: return await interaction.response.send_message("⚠️ Session expired.", ephemeral=True)
        item, map_name = purchase, self.values[0]
        player_id = get_eos_for_discord(interaction.user.id)
        if get_balance(player_id)<item['price']:
            return await interaction.response.send_message("❌ Insufficient points.", ephemeral=True)
        cmd = item['command'].replace("{implantID}", player_id).replace("{map}", map_name)
        try:
            send_rcon(cmd)
            log_transaction(player_id, -item['price'], "Success", source=f"buy:{item['name']}:{map_name}")
            await interaction.response.send_message(f"✅ Delivered {item['name']} on {map_name}.", ephemeral=True)
        except Exception:
            queue_delivery(player_id, item['name'], item['command'], map_name, item['price'])
            log_transaction(player_id, -item['price'], "Queued", source=f"buy:{item['name']}:{map_name}")
            await interaction.response.send_message(f"📦 Queued {item['name']} for {map_name}.", ephemeral=True)

class MapSelectView(View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.add_item(MapSelect(user_id))

class ShopView(View):
    def __init__(self):
        super().__init__(timeout=None)
        data = json.load(open('shop_items.json'))
        for cat, items in data.items():
            self.add_item(ShopCategoryDropdown(cat, items))
        self.add_item(Button(label="Deliver Queued", style=discord.ButtonStyle.primary, custom_id="deliver_queue"))

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.data.get('custom_id')=='deliver_queue':
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Admins only.", ephemeral=True)
        count=deliver_queued_items()
        await interaction.response.send_message(f"✅ Delivered {count} queued items.", ephemeral=True)

@bot.tree.command(name="postshop", description="Post the shop menu")
async def postshop(interaction: discord.Interaction):
    # Role-based permission check
    admin_roles = os.getenv("ADMIN_ROLE_NAMES", "Shop Admin").split(",")
    if not any(role.name in admin_roles for role in interaction.user.roles):
        return await interaction.response.send_message("❌ You don't have permission to post the shop.", ephemeral=True)
    # Proceed to post the shop menu

    await interaction.response.send_message("🛒 Shop Menu", view=ShopView())

class RetryTip4ServButton(Button):
    retry_tracker = {}
    def __init__(self, player_id, points):
        super().__init__(label=f"Retry {points}@{player_id}", style=discord.ButtonStyle.secondary)
        self.player_id=player_id; self.points=points
    async def callback(self, interaction):
        key=(interaction.user.id,self.player_id)
        import time
        now=time.time(); window=3*3600
        attempts=self.retry_tracker.get(key,[])
        attempts=[t for t in attempts if now-t<window]
        if len(attempts)>=2:
            return await interaction.response.send_message("❌ Retry limit reached.", ephemeral=True)
        attempts.append(now); self.retry_tracker[key]=attempts
        log_transaction(self.player_id,self.points,"ManualRetry",source="tip4serv")
        await interaction.response.send_message(f"✅ Retried {self.points}@{self.player_id}", ephemeral=True)
        self.disabled=True; await interaction.message.edit(view=self.view)

@bot.command(name="resetretry")
@commands.has_permissions(administrator=True)
async def resetretry(ctx, member: discord.Member, player_id: str):
    allowed=["Admin","Senior Mod"]
    if not any(r.name in allowed for r in ctx.author.roles):
        return await ctx.send("❌ No permission.")
    key=(member.id,player_id)
    if key in RetryTip4ServButton.retry_tracker:
        del RetryTip4ServButton.retry_tracker[key]
        return await ctx.send(f"🔄 Reset retry for {member.display_name}@{player_id}")
    await ctx.send(f"ℹ️ No record for {member.display_name}@{player_id}")

if not DISCORD_TOKEN:
    print("[ERROR] DISCORD_TOKEN environment variable is missing. Please set it in .env before running.")
    sys.exit(1)
bot.run(DISCORD_TOKEN)

import discord
from discord.ext import commands, tasks
from discord.ui import View, Select, Button, Modal, TextInput
import json
from db import get_eos_for_discord, get_balance, log_transaction, queue_delivery, deliver_queued_items
import os
from discord import app_commands
from mcrcon import MCRcon

SHOP_LOG_CHANNEL_ID = 123456789012345678  # Replace with your actual log channel ID

RCON_HOST = os.getenv("RCON_HOST", "127.0.0.1")
RCON_PORT = int(os.getenv("RCON_PORT", 25575))
RCON_PASSWORD = os.getenv("RCON_PASSWORD", "changeme")

REWARD_INTERVAL_MINUTES = 30  # Change to desired interval
REWARD_POINTS = 10  # Change to desired amount

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

MESSAGES = {
    "Sender": "LegendShop",
    "ReceivedPoints": "<RichColor Color=\"1, 1, 0, 1\">You have received {0} points! (total: {1})</>",
    "HavePoints": "You have {0} points",
    "NoPoints": "<RichColor Color=\"1, 0, 0, 1\">You don't have enough points</>",
    "CantGivePoints": "<RichColor Color=\"1, 0, 0, 1\">You can't give points to yourself</>",
    "SentPoints": "<RichColor Color=\"0, 1, 0, 1\">You have successfully sent {0} points to {1}</>",
    "GotPoints": "You have received {0} points from {1}",
    "NoPlayer": "<RichColor Color=\"1, 0, 0, 1\">Player doesn't exist</>",
    "FoundMorePlayers": "<RichColor Color=\"1, 0, 0, 1\">Found more than one player with the given name</>",
    "PointsCmd": "/points",
    "TradeCmd": "/trade",
}

@tasks.loop(minutes=REWARD_INTERVAL_MINUTES)
async def reward_active_players():
    for guild in bot.guilds:
        for member in guild.members:
            if not member.bot:
            eos_id = get_eos_for_discord(member.id)
            if eos_id:
                new_balance = log_transaction(eos_id, REWARD_POINTS, "IntervalReward")
                try:
                    with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                        msg = MESSAGES["ReceivedPoints"].format(REWARD_POINTS, new_balance)
                        mcr.command(f"chat {member.display_name} {MESSAGES['Sender']} {msg}")
                except Exception as e:
        print(f"Failed to send /points response via RCON: {e}")
    elif content.startswith(MESSAGES["TradeCmd"]):
                    print(f"Failed to send RCON message: {e}")

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    reward_active_players.start()

# (Rest of your code continues below without change)

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
            msg = MESSAGES["HavePoints"].format(points)
            mcr.command(f"chat {message.author.display_name} {MESSAGES['Sender']} {msg}")
        except Exception as e:
        print(f"Failed to send /points response via RCON: {e}")

        elif content.startswith(MESSAGES["TradeCmd"]):
        parts = content.split()
        if len(parts) != 3:
        return
        _, target_name, amount_str = parts
        try:
        amount = int(amount_str)
        except ValueError:
        return

        if amount <= 0:
        return

        from_user = message.author
        to_user = discord.utils.get(message.guild.members, name=target_name)
        if not to_user:
        return

        if from_user.id == to_user.id:
        return

        from_id = get_eos_for_discord(from_user.id)
        to_id = get_eos_for_discord(to_user.id)

        if not from_id or not to_id:
        return

        balance = get_balance(from_id)
        if balance < amount:
        return

        log_transaction(from_id, -amount, "TradeSent", source=f"to:{to_user.display_name}")
        log_transaction(to_id, amount, "TradeReceived", source=f"from:{from_user.display_name}")

        try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            mcr.command(f"chat {from_user.display_name} {MESSAGES['Sender']} " +
                        MESSAGES["SentPoints"].format(amount, to_user.display_name))
            mcr.command(f"chat {to_user.display_name} {MESSAGES['Sender']} " +
                        MESSAGES["GotPoints"].format(amount, from_user.display_name))
        except Exception as e:
        print(f"[RCON] Trade message error: {e}")

class ShopCategoryDropdown(Select):
    def __init__(self, category_name, items):
        options = [
        discord.SelectOption(label=item["name"], description=f"{item['price']} shop points")
        for item in items[:25]  # Max 25 options per dropdown
        ]
        super().__init__(placeholder=f"🛒 {category_name}", min_values=1, max_values=1, options=options)
        self.category = category_name
        self.items = items

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        item = next(i for i in self.items if i["name"] == selected)

        player_id = get_eos_for_discord(interaction.user.id)
        if not player_id:
        await interaction.response.send_message("⚠️ You’re not linked. Speak in CrossChat to link.", ephemeral=True)
        return

        item_command = item["command"].replace("{implantID}", player_id).replace("{map}", interaction.data.get('map', 'Unknown'))
        if "{implantID}" in item["command"] and not player_id:
        await interaction.response.send_message("⚠️ Unable to deliver: player ID (implantID) not found.", ephemeral=True)
        return

        selected_map = interaction.data.get('map')
        if not selected_map:
        await interaction.response.send_message("⚠️ Please select your current map before proceeding.", ephemeral=True)
        return

        item_command = item_command.replace("{map}", selected_map)
        interaction.client.temp_purchases[interaction.user.id] = {"item": item, "command": item_command, "map": selected_map}
        await interaction.response.send_message(
        "🌍 Please select the map you are currently on to confirm your purchase:",
        view=MapSelectDropdown(interaction.user.id),
        ephemeral=True
        )

class MapSelectDropdown(View):
    def __init__(self, user_id):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.add_item(MapSelect(user_id))

class MapSelect(Select):
    def __init__(self, user_id):
        self.user_id = user_id
        maps = ["The Island", "Scorched Earth", "Aberration", "Extinction", "Genesis", "Genesis Part 2", "Ragnarok", "Valguero", "Crystal Isles", "Fjordur"]
        options = [discord.SelectOption(label=m, value=m) for m in maps]
        super().__init__(placeholder="Select your current map", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
        await interaction.response.send_message("❌ This map selector is not for you.", ephemeral=True)
        return

        purchase = interaction.client.temp_purchases.get(interaction.user.id)
        if not purchase:
        await interaction.response.send_message("⚠️ Purchase session expired or missing.", ephemeral=True)
        return

        item = purchase["item"]
        player_id = get_eos_for_discord(interaction.user.id)
        map_name = self.values[0]

        if not player_id:
        await interaction.response.send_message("⚠️ Unable to deliver: no EOS ID found.", ephemeral=True)
        return

        balance = get_balance(player_id)
        if balance < item["price"]:
        await interaction.response.send_message("❌ You don’t have enough shop points.", ephemeral=True)
        return

        item_command = item["command"].replace("{implantID}", player_id).replace("{map}", map_name)
        try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            mcr.command(item_command)
        log_transaction(player_id, -item["price"], "Success", source=f"buy:{item['name']}:{map_name}")
        await interaction.response.send_message(f"✅ Delivered `{item['name']}` on `{map_name}`. Points deducted.", ephemeral=True)
        except Exception as e:
        queue_delivery(player_id, item["name"], item["command"], map_name, item["price"])
        log_transaction(player_id, -item["price"], "Queued", source=f"buy:{item['name']}:{map_name}")
        await interaction.response.send_message(f"📦 Player not detected. `{item['name']}` has been queued for delivery on `{map_name}`.", ephemeral=True)

@bot.tree.command(name="trade", description="Send shop points to another player")
@app_commands.describe(to_user="The Discord user to send points to", amount="The number of shop points to send")
async def trade(interaction: discord.Interaction, to_user: discord.User, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ You must send a positive number of points.", ephemeral=True)
        return

    from_user = interaction.user
    if from_user.id == to_user.id:
        await interaction.response.send_message(MESSAGES["CantGivePoints"], ephemeral=True)
        return

    from_id = get_eos_for_discord(from_user.id)
    to_id = get_eos_for_discord(to_user.id)

    if not from_id or not to_id:
        await interaction.response.send_message(MESSAGES["NoPlayer"], ephemeral=True)
        return

    balance = get_balance(from_id)
    if balance < amount:
        await interaction.response.send_message(MESSAGES["NoPoints"], ephemeral=True)
        return

    log_transaction(from_id, -amount, "TradeSent", source=f"to:{to_user.display_name}")
    log_transaction(to_id, amount, "TradeReceived", source=f"from:{from_user.display_name}")

    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
        mcr.command(f"chat {from_user.display_name} {MESSAGES['Sender']} " +
                    MESSAGES["SentPoints"].format(amount, to_user.display_name))
        mcr.command(f"chat {to_user.display_name} {MESSAGES['Sender']} " +
                    MESSAGES["GotPoints"].format(amount, from_user.display_name))
    except Exception as e:
        print(f"[RCON] Trade message error: {e}")

    await interaction.response.send_message(f"✅ Sent `{amount}` points to `{to_user.display_name}`!", ephemeral=True)

# (Rest of your file remains unchanged)

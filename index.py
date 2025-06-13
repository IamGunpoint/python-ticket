import os
import json
from flask import Flask, redirect, request, session
from discord.ext import commands
from discord import Intents, app_commands, Interaction, Embed, ButtonStyle, PermissionOverwrite
from discord.ui import Button, View, Select
from threading import Thread

TOKEN = "MTI4MDU3MzkzNzMyNzAxODA5OA.Gvt1Ak.ICFO1qu6cnw7DPDj-ve6c7wOZuUOoIF5u6HSK0"
CLIENT_ID = "1280573937327018098"
CLIENT_SECRET = "rpiYYTPWmB-LCVdqzq57_66y2_fsbJk7"
REDIRECT_URI = "https://python-ticket.onrender.com/callback"

app = Flask(__name__)
app.secret_key = os.urandom(16)

discord_oauth_url = (
    f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}&response_type=code"
    f"&scope=identify+guilds+bot+applications.commands"
)

@app.route("/")
def index():
    return f'<a href="{discord_oauth_url}">Login with Discord</a>'

@app.route("/callback")
def callback():
    return "✅ Logged in successfully. Ticket panel config coming soon."

def run_flask():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_flask).start()

intents = Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

CONFIG_PATH = "config.json"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump({}, f)
    with open(CONFIG_PATH) as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

@tree.command(name="setup", description="Setup the ticket panel")
async def setup(interaction: Interaction):
    await interaction.response.send_message("✅ Setting up ticket panel...", ephemeral=True)

    embed = Embed(title="Support Tickets", description="Choose a category to open a ticket.", color=0x5865F2)
    embed.set_footer(text="Made by IamAman")

    select = Select(placeholder="Select a category...", options=[
        discord.SelectOption(label="General Support", value="general"),
        discord.SelectOption(label="Billing", value="billing"),
        discord.SelectOption(label="Partnership", value="partner"),
    ], custom_id="ticket_category")

    view = View()
    view.add_item(select)

    await interaction.channel.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f"✅ Bot is ready as {bot.user}")
    await tree.sync()

@bot.event
async def on_interaction(interaction: Interaction):
    if interaction.type.name == "component":
        if interaction.data.get("component_type") == 3:  # Select menu
            value = interaction.data["values"][0]
            guild = interaction.guild
            user = interaction.user
            config = load_config().get(str(guild.id), {})
            category_id = config.get("category_id")
            category = guild.get_channel(category_id) if category_id else None

            overwrites = {
                guild.default_role: PermissionOverwrite(view_channel=False),
                user: PermissionOverwrite(view_channel=True)
            }

            channel = await guild.create_text_channel(
                name=f"ticket-{user.name}-{value}",
                overwrites=overwrites,
                category=category
            ) if category else await guild.create_text_channel(
                name=f"ticket-{user.name}-{value}",
                overwrites=overwrites
            )

            await interaction.response.send_message(f"🎫 Ticket created: {channel.mention}", ephemeral=True)
            await channel.send(f"👋 Hello {user.mention}, thank you for contacting {value.title()} support. A staff member will be with you shortly.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setticket(ctx, category: int):
    cfg = load_config()
    gid = str(ctx.guild.id)
    if gid not in cfg:
        cfg[gid] = {}
    cfg[gid]["category_id"] = category
    save_config(cfg)
    await ctx.send(f"✅ Ticket category set to ID {category}")

bot.run(TOKEN)

import os
import json
from flask import Flask, redirect, request, session, render_template_string
from discord.ext import commands
from discord import Intents, app_commands, Interaction, Embed, ButtonStyle
from discord.ui import Button, View
from threading import Thread

TOKEN = os.environ.get("BOT_TOKEN")  # Your bot token
CLIENT_ID = os.environ.get("CLIENT_ID")  # Discord app client ID
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT_URI = os.environ.get("REDIRECT_URI", "https://your-render-url.com/callback")

# === Flask Dashboard ===
app = Flask(__name__)
app.secret_key = os.urandom(16)

discord_oauth_url = (
    f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify+guilds+bot+applications.commands"
)

@app.route("/")
def index():
    return f'<a href="{discord_oauth_url}">Login with Discord</a>'

@app.route("/callback")
def callback():
    return "Logged in. Configure coming soon."

def run_flask():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_flask).start()

# === Discord Bot ===
intents = Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

CONFIG_PATH = "config.json"

# Load or initialize config
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
    await interaction.response.send_message("Setting up ticket panel...", ephemeral=True)

    embed = Embed(title="Support Tickets", description="Choose a category to open a ticket.", color=0x5865F2)
    embed.set_footer(text="Made by IamAman")

    btn = Button(label="Open Ticket", style=ButtonStyle.green, custom_id="open_ticket")
    view = View()
    view.add_item(btn)

    await interaction.channel.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f"Bot ready as {bot.user}")
    await tree.sync()

@bot.event
async def on_interaction(interaction: Interaction):
    if interaction.type.name == "component" and interaction.data["custom_id"] == "open_ticket":
        guild = interaction.guild
        user = interaction.user
        config = load_config().get(str(guild.id), {})
        category_id = config.get("category_id")
        category = guild.get_channel(category_id) if category_id else None
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True)
        }
        if category:
            channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites, category=category)
        else:
            channel = await guild.create_text_channel(name=f"ticket-{user.name}", overwrites=overwrites)
        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)
        await channel.send(f"Hello {user.mention}, a staff will assist you soon.")

bot.run(TOKEN)

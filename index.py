import os
import json
import threading
import http.server
import socketserver
import discord
from discord.ext import commands
from discord import Intents, app_commands, Interaction, Embed, SelectOption, PermissionOverwrite
from discord.ui import Select, View

# Start a fake HTTP server to satisfy Render
def run_fake_web():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🌐 Fake web server running on port {port}")
        httpd.serve_forever()

threading.Thread(target=run_fake_web).start()

# Bot and Discord setup
TOKEN = ""
CLIENT_ID = "1280573937327018098"

intents = Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

CONFIG_PATH = "config.json"

# Config helpers
def load_config():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump({}, f)
    with open(CONFIG_PATH) as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

# /setup command for ticket panel
@tree.command(name="setup", description="Setup the ticket panel")
async def setup(interaction: Interaction):
    await interaction.response.send_message("✅ Setting up ticket panel...", ephemeral=True)

    embed = Embed(
        title="Support Tickets",
        description="Choose a category to open a ticket.",
        color=0x5865F2
    )
    embed.set_footer(text="Made by IamAman")

    select = Select(
        placeholder="Select a category...",
        options=[
            SelectOption(label="General Support", value="general"),
            SelectOption(label="Billing", value="billing"),
            SelectOption(label="Partnership", value="partner"),
        ],
        custom_id="ticket_category"
    )

    view = View()
    view.add_item(select)

    await interaction.channel.send(embed=embed, view=view)

# /setticket command
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

# Autorole command
@tree.command(name="autorole", description="Configure auto-role for new members")
@app_commands.describe(role="Role to assign", first_join="Only assign on first join?")
async def autorole(interaction: Interaction, role: discord.Role, first_join: bool):
    cfg = load_config()
    gid = str(interaction.guild.id)
    if gid not in cfg:
        cfg[gid] = {}
    cfg[gid]["autorole"] = {"role_id": role.id, "first_join": first_join}
    save_config(cfg)
    await interaction.response.send_message(
        f"✅ Autorole set to `{role.name}` (first join only: `{first_join}`)", ephemeral=True
    )

# Apply autorole
@bot.event
async def on_member_join(member):
    cfg = load_config().get(str(member.guild.id), {}).get("autorole", {})
    if not cfg:
        return
    role = member.guild.get_role(cfg.get("role_id"))
    if role:
        await member.add_roles(role, reason="Auto-role on join")

# Ticket interaction handler
@bot.event
async def on_interaction(interaction: Interaction):
    if interaction.type.name == "component" and interaction.data.get("component_type") == 3:
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
        await channel.send(f"👋 Hello {user.mention}, thank you for contacting **{value.title()}** support. A staff member will be with you shortly.")

# Bot ready
@bot.event
async def on_ready():
    print(f"✅ Bot is ready as {bot.user}")
    print(f"🔗 Invite URL: https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot+applications.commands")
    await tree.sync()

bot.run(TOKEN)

import os
import requests
import discord
from discord.ext import commands
from discord import app_commands

# Load environment variables
TOKEN = os.environ['TOKEN_BOT']
ROBLOSECURITY_TOKEN = os.environ['ROBLOSECURITY_TOKEN']

# Check if tokens are loaded correctly
if not TOKEN:
    raise ValueError("Discord bot token not found. Please set TOKEN_BOT in the environment variables.")
if not ROBLOSECURITY_TOKEN:
    raise ValueError("Roblosecurity token not found. Please set ROBLOSECURITY_TOKEN in the environment variables.")

# Headers for authenticated Roblox requests
HEADERS = {
    'Cookie': f'.ROBLOSECURITY={ROBLOSECURITY_TOKEN}'
}

# Initialize the bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Global dictionary to hold directories
directories = {}

# Function to extract user ID from a profile link
def extract_user_id_from_profile_link(link):
    try:
        if "roblox.com/users/" in link:
            return link.split("/users/")[1].split("/")[0]
        return None
    except Exception as e:
        print(f"Error extracting user ID: {e}")
        return None

# Function to fetch username using user ID
def fetch_username(user_id):
    try:
        url = f"https://users.roblox.com/v1/users/{user_id}"
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return data.get("name", "Unknown")
    except Exception as e:
        print(f"Error fetching username: {e}")
        return None

# Function to check if a user is online
def is_user_online(user_id):
    try:
        url = "https://presence.roblox.com/v1/presence/users"
        payload = {"userIds": [user_id]}
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        presence_data = data.get("userPresences", [])
        if presence_data and presence_data[0].get("userPresenceType") == 2:
            return True
        return False
    except Exception as e:
        print(f"Error checking online status: {e}")
        return False

# Command: Add user to a directory
@bot.tree.command(name="add_user", description="Add a user to a specific directory using their profile link.")
async def add_user(interaction: discord.Interaction, directory_name: str, profile_link: str):
    user_id = extract_user_id_from_profile_link(profile_link)
    if not user_id:
        await interaction.response.send_message("Invalid profile link. Please provide a valid Roblox profile link.")
        return

    username = fetch_username(user_id)
    if not username:
        await interaction.response.send_message("Unable to fetch username. Please try again.")
        return

    if directory_name not in directories:
        directories[directory_name] = []
    directories[directory_name].append({"username": username, "profile_link": profile_link, "user_id": user_id})
    await interaction.response.send_message(f"User '{username}' added to the directory '{directory_name}'.")

# Command: Show all users in a directory
@bot.tree.command(name="show_directory", description="Show all users in a specific directory.")
async def show_directory(interaction: discord.Interaction, directory_name: str):
    if directory_name not in directories or not directories[directory_name]:
        await interaction.response.send_message(f"No users found in the directory '{directory_name}'.")
        return

    users = directories[directory_name]
    response = f"Users in '{directory_name}':\n"
    for user in users:
        response += f"- Username: {user['username']}, Profile Link: {user['profile_link']}\n"
    await interaction.response.send_message(response)

# Command: Check if users in a directory are online
@bot.tree.command(name="show_online_users", description="Show all online users in a directory.")
async def show_online_users(interaction: discord.Interaction, directory_name: str):
    if directory_name not in directories or not directories[directory_name]:
        await interaction.response.send_message(f"No users found in the directory '{directory_name}'.")
        return

    users = directories[directory_name]
    online_users = [user for user in users if is_user_online(user["user_id"])]
    if not online_users:
        await interaction.response.send_message(f"No users are currently online in the directory '{directory_name}'.")
        return

    response = f"Online users in '{directory_name}':\n"
    for user in online_users:
        response += f"- Username: {user['username']}, Profile Link: {user['profile_link']}\n"
    await interaction.response.send_message(response)

# Command: Remove user from a directory
@bot.tree.command(name="remove_user", description="Remove a user from a specific directory.")
async def remove_user(interaction: discord.Interaction, directory_name: str, username: str):
    if directory_name not in directories:
        await interaction.response.send_message(f"Directory '{directory_name}' does not exist.")
        return

    users = directories[directory_name]
    for user in users:
        if user["username"] == username:
            users.remove(user)
            await interaction.response.send_message(f"User '{username}' removed from the directory '{directory_name}'.")
            return

    await interaction.response.send_message(f"User '{username}' not found in the directory '{directory_name}'.")

# Command: Create a new directory
@bot.tree.command(name="create_directory", description="Create a new directory.")
async def create_directory(interaction: discord.Interaction, directory_name: str):
    if directory_name in directories:
        await interaction.response.send_message(f"Directory '{directory_name}' already exists.")
        return

    directories[directory_name] = []
    await interaction.response.send_message(f"Directory '{directory_name}' created successfully.")

# Command: Delete a directory
@bot.tree.command(name="delete_directory", description="Delete a directory.")
async def delete_directory(interaction: discord.Interaction, directory_name: str):
    if directory_name not in directories:
        await interaction.response.send_message(f"Directory '{directory_name}' does not exist.")
        return

    del directories[directory_name]
    await interaction.response.send_message(f"Directory '{directory_name}' deleted successfully.")

# Event: Sync commands and confirm bot is ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()
    print("Slash commands synced.")

# Run the bot
bot.run(TOKEN)

import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

role_emojis = {
    discord.PartialEmoji(name="Konoha", id=1386427115804823582): "Konoha",
    discord.PartialEmoji(name="Kumo", id=1386427146037100644): "Kumo",
    discord.PartialEmoji(name="Shinkiri", id=1386427163032551634): "Shinkiri",
    discord.PartialEmoji(name="🍃", id=None): "Unabhängige"
}

# Feste ID der Rollen-Nachricht
rollen_nachricht_id = 1386434628256268300

def emojis_equal(e1, e2):
    if e1.id and e2.id:
        return e1.id == e2.id and e1.name == e2.name
    else:
        return str(e1) == str(e2)

@bot.event
async def on_ready():
    print(f"Bot ist eingeloggt als {bot.user}")

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="willkommen")
    rollen_channel = discord.utils.get(member.guild.text_channels, name="rollenverwaltung")

    if channel and rollen_channel:
        await channel.send(
            f"Willkommen auf den SnK Discordserver, {member.mention}!\n\n"
            "Auf diesem Server kannst du mit anderen Mitgliedern des Forums in Kontakt treten, Postpartner suchen, oder einfach nur ein bisschen spammen. "
            f"Um den ganzen Server zu sehen, kannst du dir selbst im Channel <#{rollen_channel.id}> eine Rolle geben. "
            "Diese kannst du später jederzeit wechseln, indem du erneut auf das Emote klickst und ein anderes auswählst. "
            "Wenn du Charaktere in mehreren Fraktionen spielst, kannst du auch mehrere Rollen auswählen.\n\n"
            "Sobald du das erledigt hast, solltest du auch den Rest des Servers sehen. Die Quarantäne ist der allgemeine Spam, "
            "in der Postpartnersuche kannst du dir jemanden zum Schreiben suchen und im Support findest du eigentlich fast immer jemanden, "
            "der dir Fragen zur Charaktererstellung oder dem Forum an sich beantworten kann. Viel Spaß bei uns!"
        )

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id != rollen_nachricht_id or payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member is None:
        return

    emoji = payload.emoji
    for key_emoji, role_name in role_emojis.items():
        if emojis_equal(key_emoji, emoji):
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.add_roles(role)
                print(f"{member} hat die Rolle {role.name} erhalten.")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id != rollen_nachricht_id or payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if member is None:
        return

    emoji = payload.emoji
    for key_emoji, role_name in role_emojis.items():
        if emojis_equal(key_emoji, emoji):
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.remove_roles(role)
                print(f"{member} wurde die Rolle {role.name} entfernt.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content_lower = message.content.lower()
    if "döner" in content_lower:
        await message.add_reaction("🌯")
    if "keks" in content_lower:
        await message.add_reaction("🍪")

    await bot.process_commands(message)

# Startet den Bot mit dem Secret von Render (unter "Environment" → DISCORD_TOKEN eintragen)
TOKEN = os.environ['DISCORD_TOKEN']
bot.run(TOKEN)

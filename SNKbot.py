import discord
from discord.ext import commands
import json
import string
import random

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

role_emojis = {
    discord.PartialEmoji(name="Konoha", id=1386427115804823582): "Konoha",
    discord.PartialEmoji(name="Kumo", id=1386427146037100644): "Kumo",
    discord.PartialEmoji(name="Shinkiri", id=1386427163032551634): "Shinkiri",
    discord.PartialEmoji(name="🍃", id=None): "Unabhängig"
}

rollen_nachricht_id = None

def emojis_equal(e1, e2):
    if e1.id and e2.id:
        return e1.id == e2.id and e1.name == e2.name
    else:
        return str(e1) == str(e2)

@bot.event
async def on_ready():
    global rollen_nachricht_id
    print(f"Bot ist eingeloggt als {bot.user}")

    try:
        with open("rollen_message_id.txt", "r") as f:
            rollen_nachricht_id = int(f.read().strip())
            print(f"Geladene Rollen-Nachricht-ID: {rollen_nachricht_id}")
    except FileNotFoundError:
        print("Keine gespeicherte Rollen-Nachricht-ID gefunden.")

    rollen_channel = discord.utils.get(bot.get_all_channels(), name="rollenverwaltung")
    if not rollen_channel:
        print("Channel 'rollenverwaltung' nicht gefunden.")
        return

    if rollen_nachricht_id:
        try:
            await rollen_channel.fetch_message(rollen_nachricht_id)
            print("Rollen-Nachricht existiert bereits.")
            return
        except discord.NotFound:
            print("Gespeicherte Rollen-Nachricht nicht gefunden, erstelle neu.")

    text = (
        "Hol dir hier deine Rolle für den Server!\n"
        "Du brauchst mindestens eine Rolle, um alle Text- und Sprachchannels sehen zu können. "
        "Alle Rollen geben dir die gleichen Lese- und Schreibrechte – du kannst also einfach die Rolle wählen, der du dich am stärksten zugehörig fühlst.\n\n"
        "Klicke auf das entsprechende Emoji, um deine Rolle auszuwählen:\n\n"
    )
    for emoji, role_name in role_emojis.items():
        text += f"{str(emoji)}: {role_name}\n"

    message = await rollen_channel.send(text)

    for emoji in role_emojis:
        await message.add_reaction(emoji)

    rollen_nachricht_id = message.id
    with open("rollen_message_id.txt", "w") as f:
        f.write(str(rollen_nachricht_id))

    print(f"Neue Rollen-Nachricht gesendet mit ID {rollen_nachricht_id}")

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="willkommen")
    rollen_channel = discord.utils.get(member.guild.text_channels, name="rollenverwaltung")

    if channel and rollen_channel:
        await channel.send(
            f"Hey {member.mention}, schön, dass du da bist – willkommen auf dem SnK-Discord!\n\n"
            f"Damit du den ganzen Server sehen kannst, schau am besten direkt in <#{rollen_channel.id}> vorbei und gib dir eine passende Rolle. "
            "Du kannst sie jederzeit ändern oder mehrere auswählen, wenn du in mehreren Fraktionen spielst.\n\n"
            "Sobald das erledigt ist, geht’s richtig los:\n"
            "In **Quarantäne** kannst du dich austoben, in der **Postpartnersuche** findest du Schreibpartner, "
            "und im **Support** ist fast immer jemand da, der dir bei Fragen weiterhilft. Viel Spaß!"
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
    clean_text = content_lower.translate(str.maketrans('', '', string.punctuation))
    words = clean_text.split()

    # Clan-/Guide-Links via Command
    link_commands = {
        ("!jutsuslot", "!jutsuslots"): "https://www.naruto-snk.com/h9-jutsuslotrechner",
        ("!ninshu", "!jutsuregeln"): "https://www.naruto-snk.com/t7089-ninshu-jutsuregeln",
        ("!religion", "!religionen"): "https://www.naruto-snk.com/t20144-guide-religionen",
        ("!sakana", "!sakanaichizoku"): "https://www.naruto-snk.com/t13397-sakana-ichizoku",
        # Weitere URLs nach Bedarf ergänzen
    }

    for commands_tuple, url in link_commands.items():
        if content_lower.strip() in commands_tuple:
            await message.channel.send(url)
            await bot.process_commands(message)
            return

    if content_lower.startswith("!r"):
        number_part = content_lower[2:]
        if number_part.isdigit():
            sides = int(number_part)
            if sides > 0:
                result = random.randint(1, sides)
                await message.channel.send(str(result))
                await bot.process_commands(message)
                return
            else:
                await message.channel.send("Bitte gib eine Zahl größer als 0 an.")
                await bot.process_commands(message)
                return
        else:
            await message.channel.send("Bitte gib nach ! ein gültiges Kommando ein.")
            await bot.process_commands(message)
            return

    # Emoji-Reaktionen mit Pluralerkennung
    base_triggers = {
        "döner": discord.PartialEmoji(name="doener", id=1387404455946883092),
        "doener": discord.PartialEmoji(name="doener", id=1387404455946883092),
        "keks": "🍪",
        "cookie": "🍪",
        "ziege": "🐐",
        "goat": "🐐",
        "raccoon": "🦝",
        "waschbär": "🦝",
        "waschbaer": "🦝",
        "lokum": discord.PartialEmoji(name="lokum", id=1387127655517651124),
        "mogli": discord.PartialEmoji(name="mogli", id=1387158536554938518),
        "umami": discord.PartialEmoji(name="umami", id=1387396929406894090),
    }

    already_reacted = set()

    for word in words:
        if word == "ziege" and any(w.startswith("ziegel") for w in words):
            continue

        for key, emoji in base_triggers.items():
            if (
                word == key
                or word == key + "s"
                or word == key + "es"
                or word.rstrip("e") == key
                or word.rstrip("n") == key
                or word.rstrip("en") == key
                or word.rstrip("er") == key
                or word.rstrip("s") == key
            ):
                if key not in already_reacted:
                    try:
                        await message.add_reaction(emoji)
                    except Exception:
                        try:
                            await message.add_reaction(str(emoji))
                        except:
                            pass
                    already_reacted.add(key)
                    break

    await bot.process_commands(message)

@bot.command()
async def help(ctx):
    help_text = (
        "**SnK Bot Kommandos – Übersicht**\n"
        "_Verwende diese Kommandos, um direkt auf wichtige Guides zuzugreifen._\n\n"
        "**Clans und Religionen:**\n"
        "`!uchiha` – Uchiha-Clan\n"
        "`!senju` – Senju-Clan\n"
        "`!jashin` – Jashinismus\n"
        "_Hinweis: Nicht alle Clans sind hier gelistet – die Kommandos sind jedoch ähnlich aufgebaut._\n\n"
        "**Guides und Werkzeuge:**\n"
        "`!avatare` – Avatar-Übersicht\n"
        "`!gesuche` – Gesuche & Stops\n"
        "`!jutsuslot` / `!jutsuslots` – Jutsuslotrechner\n"
        "`!ninshu` / `!jutsuregeln` – Ninshu- und Jutsuregeln\n"
        "`!religion` / `!religionen` – Religions-Guide\n"
        "`!reisezeit` / `!reisezeiten` – Reisezeiten-Guide\n"
        "`!r6`, `!r20` usw. – Würfelwurf mit X Seiten\n"
    )
    await ctx.send(help_text)

# Bot starten
with open("config.json") as f:
    config = json.load(f)

bot.run(config["token"])

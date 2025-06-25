import discord
from discord.ext import commands
import json
import string
import random

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Ignoriere fehlende Commands, wenn wir sie selbst abfangen
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # Fehler ignorieren
    raise error  # Andere Fehler normal anzeigen


role_emojis = {
    discord.PartialEmoji(name="Konoha", id=1386427115804823582): "Konoha",
    discord.PartialEmoji(name="Kumo", id=1386427146037100644): "Kumo",
    discord.PartialEmoji(name="Shinkiri", id=1386427163032551634): "Shinkiri",
    discord.PartialEmoji(name="🍃", id=None): "Unabhängige"
}

rollen_nachricht_id = None  # wird geladen oder gesetzt

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

import random
import string

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
        ("!jashin", "!jashinismus"): "https://www.naruto-snk.com/t13398-jashinismus",
        ("!kemuri",): "https://www.naruto-snk.com/t17408-kemuri-ichizoku",
        ("!tsukimori",): "https://www.naruto-snk.com/t15015-tsukimori",
        ("!hozuki",): "https://www.naruto-snk.com/t13413-hozuki-ichizoku",
        ("!uchiha",): "https://www.naruto-snk.com/t13416-uchiha-ichizoku",
        ("!kaguya",): "https://www.naruto-snk.com/t13414-kaguya-ichizoku",
        ("!tensei",): "https://www.naruto-snk.com/t13415-tensei-ichizoku",
        ("!yuki",): "https://www.naruto-snk.com/t13417-yuki-ichizoku",
        ("!kasei",): "https://www.naruto-snk.com/t13419-kasei-ichizoku",
        ("!yokai",): "https://www.naruto-snk.com/t13420-yokai-ichizoku",
        ("!arashi",): "https://www.naruto-snk.com/t13418-arashi-ichizoku",
        ("!koseki",): "https://www.naruto-snk.com/t13421-koseki-ichizoku",
        ("!bakuhatsu",): "https://www.naruto-snk.com/t13422-bakuhatsu-ichizoku",
        ("!hagane",): "https://www.naruto-snk.com/t13423-hagane-ichizoku",
        ("!katoba",): "https://www.naruto-snk.com/t13424-katoba-ichizoku",
        ("!samurai", "!chang"): "https://www.naruto-snk.com/t13521-samurai-uz-chang",
        ("!mönche", "!moenche", "!hinotera"): "https://www.naruto-snk.com/t13520-monche-hi-no-tera",
        ("!inuzuka",): "https://www.naruto-snk.com/t13411-inuzuka-ichizoku",
        ("!ryojin",): "https://www.naruto-snk.com/t13410-ryojin-ichizoku",
        ("!jishaku",): "https://www.naruto-snk.com/t13409-jishaku-ichizoku",
        ("!origami",): "https://www.naruto-snk.com/t13408-origami-ichizoku",
        ("!sasagani",): "https://www.naruto-snk.com/t13407-sasagani-ichizoku",
        ("!yamanaka",): "https://www.naruto-snk.com/t13406-yamanaka-ichizoku",
        ("!uzumaki",): "https://www.naruto-snk.com/t13405-uzumaki-ichizoku",
        ("!senju",): "https://www.naruto-snk.com/t13404-senju-ichizoku",
        ("!nara",): "https://www.naruto-snk.com/t13403-nara-ichizoku",
        ("!hyuuga",): "https://www.naruto-snk.com/t13402-hyuuga-ichizoku",
        ("!akimichi",): "https://www.naruto-snk.com/t13401-akimichi-ichizoku",
        ("!aburame",): "https://www.naruto-snk.com/t13400-aburame-ichizoku",
        ("!reisezeit", "!reisezeiten"): "https://www.naruto-snk.com/t227-guide-background#390",
        ("!gesuche",): "https://www.naruto-snk.com/t222-wanted-not-wanted#376",
         ("!avatare",): "https://www.naruto-snk.com/t222-wanted-not-wanted#379",
        

    }

    for commands_tuple, url in link_commands.items():
        if content_lower.strip() in commands_tuple:
            await message.channel.send(url)
            await bot.process_commands(message)
            return


    # Wenn Nachricht mit "!r" beginnt, z.B. "!r6"
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
            await message.channel.send("Bitte gib nach ! ein gültiges Kommand ein.")
            await bot.process_commands(message)
            return

    # Emoji-Trigger mit benutzerdefinierten und Standard-Emojis
    triggers = {
        "döner": "<:doener:1387404455946883092>",
        "doener": "<:doener:1387404455946883092>",
        "keks": "🍪",
        "kekse": "🍪",
        "cookie": "🍪",
        "ziege": "🐐",
        "goat": "🐐",
        "raccoon": "🦝",
        "waschbär": "🦝",
        "waschbaer": "🦝",
        "lokum": "<:lokum:1387127655517651124>",
        "mogli": "<:mogli:1387158536554938518>",
        "umami": "<:umami:1387396929406894090>",
    }

    for word in words:
        for key, emoji in triggers.items():
            if key == word:
                # Spezialfall: "ziege" nicht in "ziegel"
                if key == "ziege" and word.startswith("ziegel"):
                    continue
                await message.add_reaction(emoji)
                break

    await bot.process_commands(message)

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)    
    
@bot.command()
async def help(ctx):
    help_text = "**SnK Bot Kommandos – Übersicht**\n"
    help_text += "_Verwende diese Kommandos, um direkt auf wichtige Guides & Clanseiten zuzugreifen._\n\n"

    command_links = {
        ("!aburame",): "Aburame-Clan",
        ("!akimichi",): "Akimichi-Clan",
        ("!arashi",): "Arashi-Clan",
        ("!avatare",): "Avatare – Wanted & Not Wanted",
        ("!bakuhatsu",): "Bakuhatsu-Clan",
        ("!chang", "!samurai"): "Samurai – Uz Chang",
        ("!gesuche",): "Gesuche – Wanted & Not Wanted",
        ("!hagane",): "Hagane-Clan",
        ("!hozuki",): "Hozuki-Clan",
        ("!hyuuga",): "Hyuuga-Clan",
        ("!inuzuka",): "Inuzuka-Clan",
        ("!jashin", "!jashinismus"): "Jashinismus",
        ("!jishaku",): "Jishaku-Clan",
        ("!jutsuslot", "!jutsuslots"): "Jutsuslot-Rechner",
        ("!kaguya",): "Kaguya-Clan",
        ("!kasei",): "Kasei-Clan",
        ("!katoba",): "Katoba-Clan",
        ("!kemuri",): "Kemuri-Clan",
        ("!koseki",): "Koseki-Clan",
        ("!mönche", "!moenche", "!hinotera"): "Mönche – Hi no Tera",
        ("!nara",): "Nara-Clan",
        ("!ninshu", "!jutsuregeln"): "Ninshu & Jutsuregeln",
        ("!origami",): "Origami-Clan",
        ("!reisezeit", "!reisezeiten"): "Reisezeiten-Guide",
        ("!religion", "!religionen"): "Religions-Guide",
        ("!ryojin",): "Ryojin-Clan",
        ("!sakana", "!sakanaichizoku"): "Sakana-Clan",
        ("!sasagani",): "Sasagani-Clan",
        ("!senju",): "Senju-Clan",
        ("!tensei",): "Tensei-Clan",
        ("!tsukimori",): "Tsukimori",
        ("!uchiha",): "Uchiha-Clan",
        ("!uzumaki",): "Uzumaki-Clan",
        ("!yamanaka",): "Yamanaka-Clan",
        ("!yokai",): "Yokai-Clan",
        ("!yuki",): "Yuki-Clan",
        ("!r [Zahl]",): "Würfeln, z. B. `!r6` für einen Wurf mit 6-seitigem Würfel",
    }

    for aliases, description in sorted(command_links.items(), key=lambda x: x[1].lower()):
        alias_list = ", ".join(aliases)
        help_text += f"`{alias_list}` → {description}\n"

    await ctx.send(help_text)


# Bot starten
with open("config.json") as f:
    config = json.load(f)

bot.run(config["token"])

import discord
from discord.ext import commands, tasks
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Ab Python 3.9
import os
import string
import random

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

from discord.ext.commands import MissingRequiredArgument, BadArgument

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, MissingRequiredArgument):
        await ctx.send("Bitte benutze das vollständige Format: `!geburtstag add @User TT.MM.`")
        return

    if isinstance(error, BadArgument):
        await ctx.send("Bitte gib einen gültigen Benutzer und ein Datum im Format TT.MM. an.")
        return

    # Wenn anderer Fehler, wirft ihn hoch
    raise error


# Geburtstagskonstanten
BIRTHDAY_FILE = "bday.json"
CONGRATS_CHANNEL_ID = 539525555276611594
REMINDER_CHANNEL_ID = 830244075264540712
MENTION_IDS = [475017022707597322, 408712490789371913]

# Neue Geburtstagsnachrichten
BIRTHDAY_MESSAGES = [
    "Woohoo! Happy Birthday, {mention}! Möge dein Tag wundervoll sein! ✨",
    "Alles Liebe zum Geburtstag, {mention}! Lass dich feiern und genieß den Kuchen! 🍰",
    "Hey {mention}, wieder ein Level-Up geschafft! Herzlichen Glückwunsch! 🎊",
    "Cheers, {mention}! Auf ein fantastisches neues Lebensjahr! 🎉",
    "Alles Gute zum Geburtstag, {mention}! 🎂 Möge dein Tag voller Freude sein!",
      "{mention}, alles Liebe zum Geburtstag! Genieße deinen besonderen Tag! 🍰",
]

def get_random_birthday_message(user):
    return random.choice(BIRTHDAY_MESSAGES).format(mention=user.mention)

def load_birthdays():
    if not os.path.isfile(BIRTHDAY_FILE):
        with open(BIRTHDAY_FILE, "w") as f:
            json.dump([], f)
        return []
    with open(BIRTHDAY_FILE, "r") as f:
        return json.load(f)

def save_birthdays(data):
    sorted_data = sorted(data, key=lambda x: x["name"].lower())  # .lower() für case-insensitive Sortierung
    with open(BIRTHDAY_FILE, "w") as f:
        json.dump(sorted_data, f, indent=4)

@bot.command(name="geburtstagsliste")
async def geburtstagsliste(ctx):
    birthdays = load_birthdays()
    if not birthdays:
        await ctx.send("Es sind noch keine Geburtstage gespeichert.")
        return

    # Monat-Namen in der richtigen Reihenfolge
    months = [
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember"
    ]

    # Geburtstage nach Monat gruppieren: Dict mit MonatIndex (1-12) als Key
    grouped = {i: [] for i in range(1, 13)}

    for entry in birthdays:
        # Datum z.B. "15.02."
        try:
            day, month, _ = entry["date"].split(".")  # z.B. "15", "02", ""
            month = int(month)
            grouped[month].append(entry)
        except Exception:
            continue  # Falls Datum falsch formatiert ist

    # Ausgabe bauen
    lines = []
    for month_idx in range(1, 13):
        entries = grouped[month_idx]
        if not entries:
            continue  # Monat überspringen, wenn keine Geburtstage

        # Monatstitel
        lines.append(f"**{months[month_idx - 1]}**")

        # Geburtstage sortiert nach Tag im Monat
        entries_sorted = sorted(entries, key=lambda e: int(e["date"].split(".")[0]))

        for entry in entries_sorted:
            name = entry.get("name", "Unbekannt")
            date = entry["date"]
            lines.append(f"{name}: {date}")

        lines.append("")  # Leerzeile zwischen Monaten

    await ctx.send("\n".join(lines))

@bot.group(name="geburtstag", invoke_without_command=True)
async def geburtstag(ctx):
    await ctx.send(
        "Verwendung:\n"
        "`!geburtstagsliste` – Alle Geburtstage anzeigen\n"
        "`!geburtstag add @User TT.MM.` – Geburtstag hinzufügen\n"
        "`!geburtstag remove @User` – Geburtstag entfernen"
    )

@geburtstag.command(name="add")
async def geburtstag_add(ctx, user: discord.Member, date: str):
    try:
        datetime.strptime(date, "%d.%m.")
    except ValueError:
        await ctx.send("Bitte gib das Datum im Format TT.MM. an.")
        return

    birthdays = load_birthdays()

    updated = False
    for entry in birthdays:
        if entry["id"] == user.id:
            entry["date"] = date
            entry["name"] = user.display_name
            updated = True
            break

    if not updated:
        birthdays.append({
            "id": user.id,
            "name": user.display_name,
            "date": date
        })

    save_birthdays(birthdays)
    await ctx.send(f"Geburtstag von {user.mention} wurde auf {date} gesetzt.")

    # Datum für heute mit Berliner Zeitzone holen
    berlin = ZoneInfo("Europe/Berlin")
    today = datetime.now(berlin).strftime("%d.%m.")

    if date == today:
        congrats_channel = bot.get_channel(CONGRATS_CHANNEL_ID)
        if congrats_channel:
            await congrats_channel.send(get_random_birthday_message(user))

@geburtstag.command(name="remove")
async def geburtstag_remove(ctx, user: discord.Member):
    birthdays = load_birthdays()
    new_birthdays = [b for b in birthdays if b["id"] != user.id]
    if len(new_birthdays) == len(birthdays):
        await ctx.send(f"Kein Eintrag für {user.mention} gefunden.")
        return

    save_birthdays(new_birthdays)
    await ctx.send(f"Geburtstag von {user.mention} wurde entfernt.")
# Hier beginnt der neue Code für bdayforum.txt

@bot.command(name="forumgeb")
async def forumgeb(ctx):
    try:
        with open("bdayforum.txt", "r", encoding="utf-8") as f:
            content = f.read()
        if content.strip():
            await ctx.send(f"```{content}```")
        else:
            await ctx.send("Die Datei bdayforum.txt ist leer.")
    except FileNotFoundError:
        await ctx.send("Die Datei bdayforum.txt wurde nicht gefunden.")

def load_bdayforum():
    """
    Liest die bdayforum.txt Datei ein und gibt eine Liste von (datum, name) tuples zurück.
    Format der Zeile: TT.MM. - Name
    Überschriften (z.B. **Monat - Monat**) werden ignoriert.
    """
    entries = []
    try:
        with open("bdayforum.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("**"):
                    continue
                if " - " in line:
                    datum, name = line.split(" - ", 1)
                    entries.append((datum.strip(), name.strip()))
    except FileNotFoundError:
        pass
    return entries

@tasks.loop(hours=24)
async def birthday_check():
    berlin = ZoneInfo("Europe/Berlin")
    today = datetime.now(berlin).strftime("%d.%m.")
    congrats_channel = bot.get_channel(CONGRATS_CHANNEL_ID)
    reminder_channel = bot.get_channel(REMINDER_CHANNEL_ID)

    if not congrats_channel or not reminder_channel:
        print("Geburtstagskanäle nicht gefunden.")
        return

     ### --- HIER: Verwaiste Geburtstage entfernen --- ###
    guild = bot.get_guild(539503573848031234)  
    if guild:
        birthdays = load_birthdays()
        valid_birthdays = []

        for entry in birthdays:
            member = guild.get_member(entry["id"])
            if member is not None:
                valid_birthdays.append(entry)
            else:
                print(f"Entferne {entry['name']} (ID {entry['id']}) aus Geburtstagsliste – nicht mehr auf dem Server.")

        if len(valid_birthdays) != len(birthdays):
            save_birthdays(valid_birthdays)
            print("Verwaiste Einträge entfernt und bday.json aktualisiert.")
    
    bdayforum_entries = load_bdayforum()

    birthdays_today = []
    for (datum, name) in bdayforum_entries:
        clean_datum = datum.strip()
        if clean_datum == today:
            birthdays_today.append(name)

    if birthdays_today:
        mentions = ' '.join(f'<@{id}>' for id in MENTION_IDS)
        msg = f"🎉 {mentions}, heute haben folgende Personen Geburtstag (Forum-Liste):\n" + "\n".join(birthdays_today)
        await reminder_channel.send(msg)
    else:
        print("Heute keine Geburtstage in bdayforum.txt.")

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

    if not birthday_check.is_running():
        birthday_check.start()

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
async def on_member_remove(member):
    birthdays = load_birthdays()
    new_birthdays = [b for b in birthdays if b["id"] != member.id]

    if len(new_birthdays) != len(birthdays):
        save_birthdays(new_birthdays)
        print(f"Geburtstagseintrag von {member} wurde entfernt, da der User den Server verlassen hat.")

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

    if not message.content.strip():  # Ignoriere leere Nachrichten (z.B. Sticker)
        return

    content_lower = message.content.lower().strip()

    # 🚫 Wenn jemand nur "!" schreibt → ignoriere
    if content_lower == "!":
        return

    clean_text = content_lower.translate(str.maketrans('', '', string.punctuation))
    words = clean_text.split()

    # Clan-/Guide-Links
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
        ("!samurai", "!uzchang"): "https://www.naruto-snk.com/t13521-samurai-uz-chang",
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
        ("!missionsverwaltung", "!missionsv"): "https://www.naruto-snk.com/t18668-missionsverwaltung",
		("!aktivitätsbonus"): "https://www.naruto-snk.com/t19433-liste-aktivitatsbonus"
    }

 
    for commands_tuple, url in link_commands.items():
        if content_lower in commands_tuple:
            await message.channel.send(url)
            await bot.process_commands(message)
            return

    if content_lower.startswith("!r"):
        number_part = content_lower[2:].strip()
        if not number_part:
            await message.channel.send("Bitte gib eine Zahl größer als 0 an.")
            await bot.process_commands(message)
            return
        if number_part.isdigit():
            sides = int(number_part)
            if sides > 0:
                result = random.randint(1, sides)
                await message.channel.send(str(result))
            else:
                await message.channel.send("Bitte gib eine Zahl größer als 0 an.")
        else:
            await message.channel.send("Bitte gib nach !r eine gültige Zahl an.")
        await bot.process_commands(message)
        return

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
                word == key or word == key + "s" or word == key + "es"
                or word.rstrip("e") == key or word.rstrip("n") == key
                or word.rstrip("en") == key or word.rstrip("er") == key
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
        "`!aktivitätsbonus` – Aktivitätenbonus-Liste\n"
        "`!avatare` – Avatar-Übersicht\n"
        "`!bonuszeit`– Aktivitätsbonus Countdown\n"
        "`!geburtstagsliste` – Geburtstagsliste\n"
        "`!geburtstag add` – Hinzufügen: Dein @ TT.MM.\n"
        "`!geburtstag remove` – Entfernen: Dein @\n"
        "`!gesuche` – Gesuche & Stops\n"
        "`!jutsuslot` / `!jutsuslots` – Jutsuslotrechner\n"
        "`!missionsverwaltung` / `!missionsv` – Missionsverwaltung\n"
        "`!ninshu` / `!jutsuregeln` – Ninshu- und Jutsuregeln\n"
        "`!religion` / `!religionen` – Religions-Guide\n"
        "`!reisezeit` / `!reisezeiten` – Reisezeiten-Guide\n"
        "`!r6`, `!r20` usw. – Würfelwurf mit X Seiten\n"
    )
    await ctx.send(help_text)
    
@bot.command(name="bonuszeit")
async def bonuszeit(ctx):
    tz = ZoneInfo("Europe/Berlin")
    first_bonus_start = datetime(2025, 6, 29, 18, 1, tzinfo=tz)
    now = datetime.now(tz)
    period = timedelta(days=14)

    if now < first_bonus_start:
        # Bonuszeit noch nicht gestartet
        await ctx.send(f"Bonuszeit startet erst am {first_bonus_start.strftime('%d.%m.%Y um %H:%M')}!")
        return

    # Berechne die Anzahl der Perioden, die komplett vergangen sind
    delta = now - first_bonus_start
    periods_passed = delta // period

    # Start der aktuellen Periode
    current_start = first_bonus_start + periods_passed * period
    # Ende ist exakt 18:00, also 1 Minute vor 18:01 des nächsten Tages nach 14 Tagen
    current_end = current_start + period - timedelta(minutes=1)
    next_start = current_end + timedelta(minutes=1)

    time_left = current_end - now

    days = time_left.days
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    await ctx.send(
         f"🕒 Der Aktivitätsbonus läuft noch **{days} Tage, {hours} Stunden und {minutes} Minuten**.\n"
        f"(Ende: {current_end.strftime('%d.%m.%Y %H:%M Uhr')})"
    )

# Bot starten
with open("config.json") as f:
    config = json.load(f)

bot.run(config["token"])

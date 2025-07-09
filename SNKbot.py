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
REMINDER_CHANNEL_ID = 886994702639984670
MENTION_IDS = [475017022707597322, 408712490789371913]

# Neue Geburtstagsnachrichten
BIRTHDAY_MESSAGES = [
    "Woohoo! Happy Birthday, {mention}! Möge dein Tag wundervoll sein! ✨",
    "Alles Liebe zum Geburtstag, {mention}! Lass dich feiern und genieß den Kuchen! 🍰",
    "Hey {mention}, wieder ein Level-Up geschafft! Herzlichen Glückwunsch! 🎊",
    "Wir beglückwünschen heute, {mention}! Auf ein fantastisches neues Lebensjahr! 🎉",
    "Alles Gute zum Geburtstag, {mention}! Möge dein Tag voller Freude sein!",
    "{mention}, alles Liebe zum Geburtstag! Genieße deinen besonderen Tag! 🍰",
    "Herzlichen Glückwunsch, {mention}! Genieß deinen Tag in vollen Zügen. 🎈",
    "Viel Freude und Glück, {mention}! Alles Gute zum Geburtstag!",
	"Alles Liebe und eine tollen Tag für dich, {mention}!",
	"Happy Birthday, {mention}! Heute wird gefeiert! 🥳",
	"Herzlichen Glückwunsch, {mention}! Mach dir einen tollen Tag! 🎂",
    "Yay! Alles Gute zum Geburtstag, {mention}! 🎊",
    "{mention}, alles Gute! Lass es krachen! 🎉",
    "{mention}, hoch die Tassen! Happy Birthday! 🎉",
    "Alles Gute zum Geburtstag, {mention}! Heute bist du der Star! ⭐"
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
async def geburtstag_add(ctx, user: discord.Member, *, date: str):
    try:
        datetime.strptime(date, "%d.%m.")
    except ValueError:
        await ctx.send("Bitte gib das Datum im Format TT.MM. an.")
        return

    birthdays = load_birthdays()

    for entry in birthdays:
        if entry["id"] == user.id:
            if entry["date"] == date:
                await ctx.send(f"{user.mention} steht bereits mit dem Datum {date} auf der Liste.")
                return
            else:
                await ctx.send(
                    f"{user.mention} ist schon mit dem Datum {entry['date']} eingetragen. "
                    f"Ich aktualisiere es auf {date}."
                )
                entry["date"] = date
                entry["name"] = user.display_name
                save_birthdays(birthdays)
                return

    # Falls User noch NICHT eingetragen
    birthdays.append({
        "id": user.id,
        "name": user.display_name,
        "date": date
    })
    save_birthdays(birthdays)
    await ctx.send(f"Geburtstag von {user.mention} wurde auf {date} gesetzt. 🎉")

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
                           
BIRTHDAY_LOG_FILE = "birthday_log.json"
BDAYFORUM_LOG_FILE = "bdayforum_log.json"

def load_birthday_log():
    try:
        with open(BIRTHDAY_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_run": "", "congratulated_users": {}}

def save_birthday_log(log):
    with open(BIRTHDAY_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4)
        
def load_bdayforum_log():
    try:
        with open(BDAYFORUM_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"last_run": ""}

def save_bdayforum_log(log):
    with open(BDAYFORUM_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4)
        
def save_bdayforum_log(log):
    with open(BDAYFORUM_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4)
       
        
@tasks.loop(hours=1)
async def birthday_check():
    berlin = ZoneInfo("Europe/Berlin")
    today = datetime.now(berlin).strftime("%d.%m.")       # ohne Jahr für Vergleich mit Geburtstagsdaten
    today_with_year = datetime.now(berlin).strftime("%d-%m-%Y")  
    congrats_channel = bot.get_channel(CONGRATS_CHANNEL_ID)
    reminder_channel = bot.get_channel(REMINDER_CHANNEL_ID)

    if not congrats_channel or not reminder_channel:
        print("Geburtstagskanäle nicht gefunden.")
        return

    # --- Verwaiste Geburtstage entfernen + Namen aktualisieren ---
    guild = bot.get_guild(539503573848031234)
    valid_birthdays = []
    if guild:
        birthdays = load_birthdays()
        names_updated = False

        for entry in birthdays:
            try:
                member = await guild.fetch_member(entry["id"])
            except discord.NotFound:
                member = None

            if member:
                # Display-Name vergleichen
                if entry.get("name") != member.display_name:
                    print(f"Name geändert: {entry['name']} ➜ {member.display_name}")
                    entry["name"] = member.display_name
                    names_updated = True
                valid_birthdays.append(entry)
            else:
                print(f"Entferne {entry['name']} (ID {entry['id']}) aus Geburtstagsliste – nicht mehr auf dem Server.")

        if names_updated or len(valid_birthdays) != len(birthdays):
            save_birthdays(valid_birthdays)
            print("bday.json aktualisiert (Namen/Einträge).")
    else:
        valid_birthdays = load_birthdays()

    # --- Forum Reminder nur einmal am Tag senden ---
    forum_log = load_bdayforum_log()
    if forum_log.get("last_run") != today_with_year:
        bdayforum_entries = load_bdayforum()
        birthdays_today = []

        for (datum, name) in bdayforum_entries:
            if datum.strip() == today:
                birthdays_today.append(name)

        if birthdays_today:
            mentions = ' '.join(f'<@{id}>' for id in MENTION_IDS)
            msg = (
                f"🎉 {mentions}, heute haben folgende Personen Geburtstag (Forum-Liste):\n"
                + "\n".join(birthdays_today)
            )
            await reminder_channel.send(msg)
        else:
            print("Heute keine Geburtstage in bdayforum.txt.")

        forum_log["last_run"] = today_with_year
        save_bdayforum_log(forum_log)
    else:
        print("Forum-Reminder heute schon gesendet.")

    # --- Geburtstagskinder heute (bday.json) gratulieren ---
    birthday_log = load_birthday_log()

    # Reset, wenn neuer Tag (mit Jahr!)
    if birthday_log["last_run"] != today_with_year:
        birthday_log["last_run"] = today_with_year
        birthday_log["congratulated_users"] = {}

    for entry in valid_birthdays:
        user_id = str(entry["id"])
        if entry["date"] == today and user_id not in birthday_log["congratulated_users"]:
            member = guild.get_member(entry["id"]) if guild else None
            if member:
                await congrats_channel.send(get_random_birthday_message(member))
                birthday_log["congratulated_users"][user_id] = today_with_year

    save_birthday_log(birthday_log)

    print(f"birthday_log.json und bdayforum_log.json aktualisiert (last_run: {today_with_year})")

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

    if not message.content.strip():
        return

    content = message.content.strip()
    content_lower = content.lower()

    # 🚫 Nur "!" oder "! " ignorieren
    if content == "!" or content == "! ":
        return

    # --- Wenn Nachricht mit "!" beginnt: Command- oder Link-Shortcut ---
    if content_lower.startswith("!"):
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
		("!aktivitätsbonus"): "https://www.naruto-snk.com/t19433-liste-aktivitatsbonus",
        ("!bijuukontrolle"): "https://www.naruto-snk.com/t13426-biju-kontrolle",
        ("!jikukan"): "https://www.naruto-snk.com/t13436-jikukan-ninjutsu",
        ("!kugutsu"): "https://www.naruto-snk.com/t13435-kugutsu-ninjutsu",
        ("!fuin"): "https://www.naruto-snk.com/t13434-fuinjutsu",
        ("!senjutsu"): "https://www.naruto-snk.com/t13432-senjutsu",
        ("!kekkai"): "https://www.naruto-snk.com/t13430-kekkai-ninjutsu",
        ("!kt", "!kanchitaipu"): "https://www.naruto-snk.com/t13429-kanchi-taipu",
        ("!iryo"): "https://www.naruto-snk.com/t13428-iryoninjutsu",
        ("!ht", "!hachimontonko"): "https://www.naruto-snk.com/t13427-hachimon-tonko",
        ("!grundjutsu"): "https://www.naruto-snk.com/t305-akademiejutsu-grundwissen",
        ("!suiton"): "https://www.naruto-snk.com/t311-suiton-ninjutsu",
        ("!raiton"): "https://www.naruto-snk.com/t309-raiton-ninjutsu",
        ("!doton"): "https://www.naruto-snk.com/t310-doton-ninjutsu",
        ("!fuuton"): "https://www.naruto-snk.com/t308-fuuton-ninjutsu",
        ("!katon"): "https://www.naruto-snk.com/t307-katon-ninjutsu",
        ("!kinjutsu"): "https://www.naruto-snk.com/t293-kinjutsu",
        ("!taijutsu"): "https://www.naruto-snk.com/t313-taijutsu",
        ("!haar"): "https://www.naruto-snk.com/t14680-haartechniken",
        ("!tinte"): "https://www.naruto-snk.com/t15597-tintentechniken",
        ("!genjutsu"): "https://www.naruto-snk.com/t312-genjutsu",
        ("!lwaffen"): "https://www.naruto-snk.com/t16234-legendare-waffen",
        ("!eninjutsu"): "https://www.naruto-snk.com/t306-elementlose-ninjutsu",
        ("!shurikenjutsu"): "https://www.naruto-snk.com/t20557-shurikenjutsu",
             ("!ningurechner",): "https://www.naruto-snk.com/h10-ningu-rechner",
        }

        for commands_tuple, url in link_commands.items():
            if content_lower in commands_tuple:
                await message.channel.send(url)
                return

        if content_lower.startswith("!r"):
            number_part = content_lower[2:].strip()
            if not number_part:
                await message.channel.send("Bitte gib eine Zahl größer als 0 an.")
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
            return

        await bot.process_commands(message)
        return

    clean_text = content_lower.translate(str.maketrans('', '', string.punctuation))
    words = clean_text.split()

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

@bot.command(aliases=['hilfe'])
async def help(ctx):
    help_text = (
        "**SnK Bot Kommandos – Übersicht**\n"
        "_Verwende diese Kommandos, um direkt auf wichtige Guides zuzugreifen._\n\n"
        "**Clans und Religionen:**\n"
        "`!uchiha` – Uchiha-Clan\n"
        "`!senju` – Senju-Clan\n"
        "`!jashin` – Jashinismus\n"
        "_Hinweis: Nicht alle Clans sind hier gelistet – die Kommandos sind jedoch ähnlich aufgebaut._\n\n"
        "**Ausbildungen:**\n"
         "`!bijuukontrolle` - Bijuu-Kontrolle\n"
        "`!hachimontonko` / `!ht` - Hachimon Tonko\n"
        "`!iryo` - Iryouninjutsu\n"
         "`!jikukan` - Jikukan Ninjutsu\n"
         "`!kanchitaipu` / `!kt` - Kanchi Taipu\n"
         "`!kekkai` - Kekkai Ninjutsu\n"
         "`!kugutsu` - Kugutsu Ninjutsu\n"
         "`!senjutsu` - Senjutsu\n\n"
		"**Jutsulisten:**\n"
        "`!doton` - Doton-Techniken\n"
        "`!eninjutsu` - Elementlose Ninjutsu\n"
        "`!fuuton` - Fuuton-Techniken\n"
         "`!genjutsu` - Genjutsu\n"
        "`!grundjutsu` - Akademiejutsu & Grundwissen\n"
         "`!haar` - Haar-Techniken\n"
         "`!katon` - Katon-Techniken\n"
        "`!kinjutsu` - Limitierte Künste\n"
     	 "`!raiton` - Raiton-Techniken\n"
         "`!shurikenjutsu` - Shurikenjutsu\n"
         "`!suiton` - Suiton-Techniken\n"
        "`!taijutsu` - Taijutsu\n"
        "`!tinte` - Tinten-Techniken\n\n"
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
          "`!ningurechner` – Ningu Rechner\n"
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

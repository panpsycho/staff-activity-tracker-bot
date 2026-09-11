import os
from dotenv import load_dotenv
import time
import discord
import csv
import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
guild = None
staff_role = None

#These files MUST have one line of blankspace at the end.
voice_file = "voice.csv"
staff_file = "staff.csv"
totals_file = "totals.csv"
notes_file = "notes.csv"

def get_week_file(week_num=None):
    if week_num is None:
        week_num = get_week_num()
    return f"week_{week_num}.csv"

starting_date = datetime.datetime(2026, 9, 7)

DISBOARD_BOT_ID = 302050872383242240
SERVER_ID = 924425431048917033

#The columns at which these things appear in the database.
ID_COL = 0
VERIFICATIONS_COMPLETED_COL = 1
KICKS_COL = 2
BANS_COL = 3
TIMEOUTS_COL = 4 
MESSAGES_COL = 5
VC_TIME_COL = 6
BUMPS_COL = 7
NOTES_COL = 8

#COMMANDS:
# ?totals <staff_id> --- displays the total stats for all staff members (unless staff_id is provided, at which point only data for that staff is provided)
# ?week X <staff_id> --- displays the week_x stats for all staff members (unless staff_id is provided, at which point only data for that staff is provided)
# ?currentweek --- displays the current week
# ?addnote <note> --- adds a note for that week
# ?viewnote <week_num> <staff_id> --- view all notes for that week, optionally from a staff member

def is_staff(member):
    return staff_role in member.roles

def get_week_num():
    difference = datetime.datetime.now() - starting_date
    return 1 + difference.days // 7

async def receive_commands(message):

    msg = message.content.split(" ")
    length = len(msg)

    command = msg[0]

    match command:
        case "?addnote":
            if not is_staff(message.author):
                return
            msg = " ".join(msg[1:])

            with open(notes_file, mode="a", encoding="utf-8", newline="") as file:
                csv_writer = csv.writer(file)
                csv_writer.writerow([message.author.id, get_week_num()] + [msg])
            await message.channel.send("Stored note :3")
            pass
        case "?viewnote":
            with open(notes_file, mode="r", encoding="utf-8", newline="") as file:
                csv_reader = csv.reader(file)
                data = list(csv_reader)

            output = ""
            
            #if length == 2:
            for row in data:
                if (length == 2 and row[1] == msg[1]) or (length == 3 and row[1] == msg[1] and row[0] in msg[2]):
                    user_name = (await client.fetch_user(int(row[0]))).name
                    output += " ".join([user_name] + row[2:]) + "\n\n"
            # elif length == 3:
            #     for row in data:
            #         if row[1] == msg[1] and row[0] in msg[2]:
            #             user_name = (await client.fetch_user(int(row[0]))).name
            #             output += " ".join([user_name] + row[2:]) + "\n\n"
            
            if not output:
                output = "ERROR: No messages found for that week"
            
            await message.channel.send(output)
            pass
        case "?helpme":
            msg = "#COMMANDS:\n\n?helpme --- displays info about each command\n\n?totals <staff_id> --- displays the total stats for all staff members (unless staff_id is provided, at which point only data for that staff is provided)\n\n?week X <staff_id> --- displays the week_x stats for all staff members (unless staff_id is provided, at which point only data for that staff is provided)\n\n?currentweek --- displays the current week\n\n?addnote <note> --- adds a note for the current week\n\n?viewnote <week_num> <staff_id> --- view all notes for that week, optionally from a staff member"
            await message.channel.send(msg)
            pass
        case "?currentweek":
            await message.channel.send(f"Week {get_week_num()}")
            pass
        case "?totals":
            if length == 1:
                # TODO
                #Display ALL totals
                data = get_totals_data()
                await send_csv_message(data, message.channel)
                pass
            elif length == 2:
                # TODO
                #Display totals only for this staff
                data = get_totals_data()
                data = [row for row in data if row[0] in msg[1]]
                await send_csv_message(data, message.channel)
                pass
            else:
                pass
                #print("ERROR: Invalid number of arguments for command 'totals'")
            pass
        case "?week":
            if length == 2:
                # TODO
                #Display week X statistics for  ll staff
                data = get_week_data(msg[1])
                if data == None:
                    await message.channel.send("ERROR: Unable to fetch data for that week")
                    return
                await send_csv_message(data, message.channel)
                pass
            elif length == 3:
                #TODO
                #Display week X statistics for one staff specifically
                data = get_week_data(msg[1])
                if data == None:
                    await message.channel.send("ERROR: Unable to fetch data for that week")
                    return
                data = [row for row in data if row[0] in msg[2]]
                await send_csv_message(data, message.channel) 
                pass
            else:
                pass
                #print("ERROR: Invalid number of arguments for command 'week'")
            pass
        case _:
            #Not a command. Pass.
            pass

def get_week_data(week_num):
    if int(week_num) > get_week_num():
        #print("ERROR: Cannot give week data for a future week.")
        return

    check_for_week_file(week_num)
    
    with open(get_week_file(week_num), mode="r", encoding="utf-8", newline="") as file:
        csv_reader = csv.reader(file)
        data = list(csv_reader)

    return data

def get_totals_data():
    
    with open(totals_file, mode="r", encoding="utf-8", newline="") as file:
        csv_reader = csv.reader(file)
        data = list(csv_reader)

    return data

async def send_csv_message(data, channel):

    msg = "NAME     VERIFS     KICKS     BANS     TIMEOUTS     MESSAGES     VC_SECONDS     BUMPS\n"

    for row in data:
        row[0] = (await client.fetch_user(int(row[0]))).name #guild.get_member(int(row[0])).name
        msg += ",        ".join(row) + "\n"

    await channel.send(msg)



    


@client.event
async def on_ready():
    global guild
    guild = client.get_guild(SERVER_ID)


    #print(guild)

    #Prepare staff.csv and set up other files
    global staff_role
    staff_role = None
    for role in guild.roles:
        if role.name == "Staff":
            staff_role = role

    if not staff_role:
        #print("ERROR: Could not find a 'Staff' role")
        return


    #Check to see that staff.csv and voice.csv have all staff members
    #If they do not, add them.

    with open(staff_file, mode="r", encoding="utf-8", newline="") as file:
        csv_reader = csv.reader(file)
        data = list(csv_reader)

    #print(len(data))

    missing_members = []
    staff_file_ids = [int(data[i][0]) for i in range(len(data))]

    for member in staff_role.members:
        if member.id not in staff_file_ids:
            missing_members.append(member)

    if missing_members:
        with open(staff_file, mode="a", encoding="utf-8", newline="") as file:
            csv_writer = csv.writer(file)
            for member in missing_members:
                csv_writer.writerow([member.id])


    with open(voice_file, mode="r", encoding="utf-8", newline="") as file:
        csv_reader = csv.reader(file)
        data = list(csv_reader)

    missing_members = []
    staff_file_ids = [int(data[i][0]) for i in range(len(data))]

    for member in staff_role.members:
        if member.id not in staff_file_ids:
            missing_members.append(member)

    if missing_members:
        with open(voice_file, mode="a", encoding="utf-8", newline="") as file:
            csv_writer = csv.writer(file)
            for member in missing_members:
                #Double check this's interaction with VC functionality
                csv_writer.writerow([member.id, -1])


    with open(totals_file, mode="r", encoding="utf-8") as file:
        csv_reader = csv.reader(file)
        data = list(csv_reader)

    missing_members = []
    staff_file_ids = [int(data[i][0]) for i in range(len(data))]

    for member in staff_role.members:
        if member.id not in staff_file_ids:
            missing_members.append(member)

    with open(totals_file, mode="a", encoding="utf-8", newline="") as file:
        csv_writer = csv.writer(file)
        for member in missing_members:
            csv_writer.writerow([member.id, 0, 0, 0, 0, 0, 0, 0])
    


@client.event
async def on_message(message):

    #Ignore my own messages
    if message.author == client.user:
        return

    if message.author.id == DISBOARD_BOT_ID:
        if message.interaction is not None:
            user = message.interaction.user
            command_name = message.interaction.name
            if not is_staff(user):
                return
            
            if command_name == "bump":
                increment_bump_count(user)

    await receive_commands(message)

    if not is_staff(message.author):
        return

    #print("staff sent message")

    if message.content == "?va" or message.content == "?vm":
        increment_verification_count(message.author)

    increment_message_count(message.author)


#Compute how long the member has been VCing, update their VC hours accordingly
@client.event
async def on_voice_state_update(member, before, after):

    if not is_staff(member):
        return

    #VoiceState changes from mutes, etc... these are irrelevant to duration.
    if before.channel == after.channel: 
        return

    #If they go from inactive to active, track the timestamp at which this occurs.
    #If they go from active to inactive, use the saved timestamp as well as the current timestamp 
    #   to compute the length of this duration, and add this to the database

    
    with open(voice_file, mode="r", encoding="utf-8", newline="") as file:
        csv_reader = csv.reader(file)
        data = list(csv_reader)

    row_to_change = -1
    current_row = 0
    for row in data:
        if int(row[0]) == member.id:
            row_to_change = current_row
            break
        current_row += 1

    if row_to_change == -1:
        #print(f"ERROR: Cannot find staff's voice data in {voice_file}")
        pass

    updated_row = [-1, -1]

    if before.channel == None and after.channel != None: #Join VC
        updated_row = [member.id, time.time()]
    elif before.channel != None and after.channel == None: #Leave VC
        updated_row = [member.id, -1]

        duration = time.time() - float(data[row_to_change][1])

        if duration > 24 * 60 * 60: #If duration > than 24 hours because i know some of yall are freaks
            return

        increment_voice_duration(member, duration)
    else: #You switched from one voice channel to another, didn't you... >:(
        updated_row = [member.id, time.time()]

        duration = time.time() - float(data[row_to_change][1])
        increment_voice_duration(member, duration)
        pass

    data[row_to_change] = updated_row

    with open(voice_file, mode="w", encoding="utf-8", newline="") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(data)

@client.event
async def on_audit_log_entry_create(entry):
    #print(entry.action) #Make sure that entry.action is actually a string
    match entry.action:
        case discord.AuditLogAction.kick:
            increment_kick_count(entry.user)
            pass
        case discord.AuditLogAction.ban:
            increment_ban_count(entry.user)
            pass
        case discord.AuditLogAction.member_update:
            if not entry.before.timed_out_until and entry.after.timed_out_until: #Double check value when not timed out
                if not entry.user:
                    #print("Timeout applied without a member who did so (system/automod?)")
                    return
                increment_timeout_count(entry.user)
            pass
        case discord.AuditLogAction.member_role_update:
            if staff_role not in entry.before.roles and staff_role in entry.after.roles:
                #Person gained a staff role, update totals and current week CSV.

                #print(1)

                def add_member_to_file(filename, row_to_add):
                    #print(row_to_add)
                    with open(filename, mode="r", encoding="utf-8", newline="") as file:
                        csv_reader = csv.reader(file)
                        data = list(csv_reader)

                    found = False
                    for row in data:
                        if int(row[0]) == entry.target.id:
                            found = True
                            break

                    if not found:
                        with open(filename, mode="a", encoding="utf-8", newline="") as file:
                            csv_writer = csv.writer(file)
                            csv_writer.writerow(row_to_add)

                add_member_to_file(totals_file, [entry.target.id, 0, 0, 0, 0, 0, 0, 0])
                add_member_to_file(get_week_file(), [entry.target.id, 0, 0, 0, 0, 0, 0, 0])
                add_member_to_file(voice_file, [entry.target.id, -1])
                add_member_to_file(staff_file, [entry.target.id])
            pass
        case _:
            #print("Unknown")
            return


### UPDATING DATABASE ###

def increment_column(member, column_index, optional_amount=None, optional_replace=None):
    with open(totals_file, mode="r", encoding="utf-8", newline="") as file:
        csv_reader = csv.reader(file)
        data = list(csv_reader)

    row_index = -1
    current_index = 0
    for row in data:
        if row[0] == str(member.id):
            row_index = current_index
            break
        current_index += 1

    if row_index == -1:
        #print(f"ERROR: Unable to find member's ID in {totals_file}")
        return

    # if not optional_replace:
    #     increment_amount = 1 if not optional_amount else optional_amount
    #     data[row_index][column_index] = float(data[row_index][column_index]) + increment_amount
    # else:
    #     data[row_index][column_index] = optional_replace

    increment_amount = 1 if not optional_amount else optional_amount
    data[row_index][column_index] = float(data[row_index][column_index]) + increment_amount

    with open(totals_file, mode="w", encoding="utf-8", newline="") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(data)


    week_file = get_week_file()
    check_for_week_file()

    with open(week_file, mode="r", encoding="utf-8", newline="") as file:
        csv_reader = csv.reader(file)
        data = list(csv_reader)

    row_index = -1
    current_index = 0
    for row in data:
        if row[0] == str(member.id):
            row_index = current_index
            break
        current_index += 1

    if row_index == -1:
        #print(f"ERROR: Unable to find member's ID in {week_file}")
        return

    increment_amount = 1 if not optional_amount else optional_amount
    data[row_index][column_index] = float(data[row_index][column_index]) + increment_amount

    with open(week_file, mode="w", encoding="utf-8", newline="") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerows(data)

def increment_message_count(member):
    #print(f"incrementing message for {member.name}")
    increment_column(member, MESSAGES_COL)


def increment_voice_duration(member, duration):
    duration = int(duration)
    #print(f"incrementing vc duration for {member.name} with duration {duration}")
    increment_column(member, VC_TIME_COL, duration)


def increment_kick_count(member):
    #print(f"incrementing kick count for {member.name}")
    increment_column(member, KICKS_COL)


def increment_ban_count(member):
    #print(f"incrementing ban count for {member.name}")
    increment_column(member, BANS_COL)


def increment_timeout_count(member):
    #print(f"incrementing timeout count for {member.name}")
    increment_column(member, TIMEOUTS_COL)


def increment_bump_count(member):
    #print(f"incrementing bump count for {member.name}")
    increment_column(member, BUMPS_COL)


def increment_verification_count(member):
    #print(f"incrementing verification counts for {member.name}")
    increment_column(member, VERIFICATIONS_COMPLETED_COL)


def register_note(member, note):
    #TODO
    pass

def check_for_week_file(week_num=None):
    week_file_name = get_week_file(week_num)
    if os.path.isfile(week_file_name) and os.path.getsize(week_file_name) > 0: #Does this work?
        return

    #File does not exist, create it.

    #BUG: Beware, the file may exist but be empty, and thus bypass writing people's IDs into the file!!!

    with open(week_file_name, "w", encoding="utf-8", newline="") as file:
        csv_writer = csv.writer(file)
        for member in guild.members:
            if is_staff(member):
                csv_writer.writerow([member.id, 0, 0, 0, 0, 0, 0, 0])


client.run(TOKEN)
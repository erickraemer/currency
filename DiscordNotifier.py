#!python3
import discord
import sys
import datetime
import traceback

client = discord.Client()


def main():
    if len(sys.argv) != 5:
        return 1

    global message, prefix, channel_name
    message = "{}\n{}".format(sys.argv[2], sys.argv[1])
    prefix = sys.argv[2]
    channel_name = sys.argv[3]
    token = sys.argv[4]

    client.run(token)
    return


@client.event
async def on_ready():
    channel = find_channel()
    if not channel:
        return 1

    try:
        msg = await find_last_message(channel)
        if msg:
            await msg.edit(content=message)
        else:
            await channel.send(content=message)
    except:
        print(traceback.format_exc(), file=sys.stderr)
    finally:
        await client.logout()
        await client.close()
    return


def find_channel():
    for c in client.get_all_channels():
        if c.name == channel_name:
            return c
    return None


def is_last_message(msg):
    return (msg.author == client.user and
            msg.created_at.date() == datetime.date.today() and
            msg.content.startswith(prefix))


async def find_last_message(channel):
    async for msg in channel.history(limit=50):
        if is_last_message(msg):
            return msg
    return None


main()

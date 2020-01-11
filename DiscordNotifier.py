#! python3
from datetime import datetime, timezone, date
from operator import itemgetter
import discord
import sys
import traceback
import re

client = discord.Client()


def main():
    if len(sys.argv) != 5:
        return 1

    global message, prefix, channel_name
    message = sys.argv[1]
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
        update = string_to_dict(message)
        if msg:
            score = string_to_dict(msg.content[len(prefix) + 1:])
            update_score(score, update)
            await msg.edit(content="{}\n{}".format(prefix, dict_to_string(score)))
        else:
            await channel.send(content="{}\n{}".format(prefix, dict_to_string(update)))
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
            utc_to_local(msg.created_at).date() == date.today() and
            msg.content.startswith(prefix))


async def find_last_message(channel):
    async for msg in channel.history(limit=50):
        if is_last_message(msg):
            return msg
    return None


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)


def string_to_dict(s: str) -> dict:
    s = re.sub('[^a-zA-Z0-9_:,-]', '', s).strip()
    lop = s.split(',')
    d = dict()
    for p in lop:
        pair = p.split(':')
        d[pair.pop()] = int(pair.pop())
    return d


def dict_to_string(d: dict) -> str:
    return ",  ".join(": ".join((k, "+{}".format(v) if v > 0 else str(v))) for k, v in
                      sorted(d.items(), key=itemgetter(1), reverse=True))


def update_score(d1: dict, d2: dict):
    for k, v in d2.items():
        i = d1.get(k, 0) + v
        if i == 0:
            d1.pop(k, None)
        else:
            d1[k] = i
    return


main()

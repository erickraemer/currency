import discord
import sys
import datetime

client = discord.Client()


def main():
    if len(sys.argv) != 5:
        return 1

    global message, prefix, channel
    message = "{}\n{}".format(sys.argv[2], sys.argv[1])
    prefix = sys.argv[2]
    channel = sys.argv[3]
    token = sys.argv[4]

    client.run(token)
    print("closed")
    return


@client.event
async def on_ready():
    print("logged in")
    for c in client.get_all_channels():
        if c.name == channel:
            print("found channel: {}".format(channel))
            async for msg in c.history(limit=100):
                if (msg.author == client.user and
                        msg.content.startswith(prefix) and
                        msg.created_at.date() == datetime.date.today()):
                    print("editing message")
                    await msg.edit(content=message)
                    break
                else:
                    print("sending message")
                    await c.send(content=message)
                    break
            await client.logout()
            await client.close()
    return


main()

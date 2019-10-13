# Currency
An enhancement script for the streamlabs loyality system which rewards your viewers with points for watching your stream.

## Features
- Custom point amount and frequency
- Ignores lurking bots
- Adds a point decay system
- Adds message events about scored points

## How Does It Work
Currency does only give points to viewers which already have at least one point or
are following. To exlcude already present bots you need to reset their score to zero.
With point rewards for donations, subs or hosts on the streamlabs website and the chatbot currency settings, you can further 
control which action is requiered to receive points for watching your stream. For a viewer to receive points he needs to
write in chat at least once within 15 minutes before payout. This way bots are kept out from earning points on your channel.

## How To Install
[Please follow this tutorial](https://github.com/StreamlabsSupport/Streamlabs-Chatbot/wiki/Prepare-&-Import-Scripts).
After that you can adjust all settings by clicking on the script name in the chatbots script section.

## The Decay System
The decay system will punish viewers which are inactive over 
larger peroids of time. Viewers can reset their decay counter by writing a message in chat.

### Top X
Specifies how many viewers will be affected by the decay system. 

### Decay Types
There're two types of decay options:
- Fixed: Viewers will always lose a fixed percentage of points which can be 
adjusted with the "Decay Amount" slider.
- Stacking: Viewers will lose 1% more points as on the last decay. This means on 
the first decay a viewer will lose 1%, on the next 2% and so on until he drops out
of your selected "Top X" or resets his decay counter by writing something in chat.

### Announce Payout In Chat
This option will send a chat message with all viewers which received points on the payout (whithout mentioning them).
No message will be send if no viewer received points.

### Send Score Summary To Discord
Currency will send a score summary to your discord server. Currently you need to hit the "Reload Scripts" button for this
to work at the end of your stream. The reason for this is because the chatbot will take very long to detect that your stream is offline and most users will
probably close the chatbot beforehand. Also for this to work you need to setup a discord bot in the streamlabs chatbot settings menu. 

## Logging
Currency automatically creates a logfile "currency.log" in its script folder after your stream goes live.

## Planned Features & Problems
- Track points for subs, donations and hosts
   - What happens if someone subs while the stream is offline.
   - Rewards amounts cant be requested from the chatbot.
   
- Detect close and send score summary automatically to discord
   - Bot takes way to long to notice
   - Bot does not run 24/7
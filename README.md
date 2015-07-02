# Twitch PyBot
A bot scripted in Python for use on personal twitch channels.

# Setup and (Lack of) Documentation
This project is still in it's infancy. You'll need minimal knowledge of editing and handling .xml files. If you wan't to add features you'll need to know how to program things in Python. As of now there is no documentation.

# Features
- Make as many customs commands as you want within the config.xml
  - Set whether they are sub only commands or not
  - Use ${USER}$ to refer to the user that called the command (more tags to come as I think of useful ones)
  - Set custom cooldown times (*i.e.* the time necessary between each successive call of the command)
- Designate who can access your master commands (*i.e.* !ban, !unban, etc.)
  - Can pick and choose from mods, global mods, admins, and staff
- Relatively easy to configure. Simply make a twitch account for your bot and get your oauth token

#Requirements
- Python 3.4 or higher
- Basic xml knowledge (pretty self-explanatory)
- Python programming knowledge if you want to hard code your own custom feature into the bot.
- Run it on the computer that you stream on, or get a free shell account and run the bot from there.

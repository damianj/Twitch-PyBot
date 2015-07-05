# Twitch PyBot
A bot scripted in Python for use on personal twitch channels. It uses a JSON file to load in all it needs to know to get set up, this file also stores the custom commands the user can assign to it.

# Getting started
You'll need minimal knowledge of editing and handling .json files. If you wan't to add features you'll need to know how to program things in Python. As of now there is no documentation.

# Features
- Make as many customs commands as you want within the config.json
  - Set whether they are sub only commands or not
  - Use ${USER}$ to refer to the user that called the command
  - Use ${UPTIME}$ to return  the current uptime of the stream. (use !settime if bot was started before stream)
  - Set custom cooldown times (*i.e.* the time necessary between each successive call of the command)
  - Set whether commands are sub-only or can be used by anyone in chat
- Can also use the !addcmd and !remcmd commands when the bot is in an IRC channel to add and remove commands from the JSON file
  - **!addcmd|!examplecommand|Example response for the command|5|False**
    - !*[call command]*|!*[command name]*|*[response text]*|*[cooldown]*|*[sub-only]*
  - **!remcmd !examplecommand**
    - !*[call command]* !*[name of the command to remove]*
- Designate who can access your master commands (*i.e.* !ban, !unban, etc.)
  - Can pick and choose from mods, global mods, admins, and staff
- Relatively easy to configure. Simply make a twitch account for your bot and get your oauth token

#Requirements
- Python 3.4 or higher
- Basic JSON knowledge to handle and edit the config file. Plenty of online editors can help you get started.
- Python programming knowledge if you want to hard code your own custom feature into the bot.
- Run it on the computer that you stream on, or get a free shell account and run the bot from there.

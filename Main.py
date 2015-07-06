from CommonAssets import GeneralFunctions as Gen_Tools
from TwitchBot import TwitchBot


def main(twitch_bot):
    twitch_bot.start()
    while True:
        irc_msg = twitch_bot.irc_socket.recv(1024).decode("UTF-8").strip('\n\r')
        twitch_bot.logger.info('[IRC CHAT LOG]: {0}'.format(irc_msg).replace('\n', '\n\t'))
        if twitch_bot.irc_maps.irc_probe[0] in irc_msg:
            s = irc_msg.split(';')
            try:
                user = s[1].strip()[13:]
            except IndexError:
                user = s[5].split(':')[1].split('!')[0]
            twitch_bot.command(user, irc_msg, Gen_Tools.str_to_bool(s[3][11:]),
                               Gen_Tools.str_to_bool(s[5].split(':')[0][10:].replace(' ', '')
                                                     if s[5].split(':')[0][10:].replace(' ', '') != ''
                                                     else user.lower(), twitch_bot.settings.master_access))
        elif twitch_bot.irc_maps.irc_probe[1] in irc_msg:
            twitch_bot.ping(irc_msg.split()[1])
        elif twitch_bot.irc_maps.irc_probe[2] in irc_msg or twitch_bot.irc_maps.irc_probe[3] in irc_msg:
            twitch_bot.logger.error('Error logging in: Please verify the oauth key and bot account name\n'
                                    '\tClosing the connection and exiting the program.')
            twitch_bot.irc_socket.close()
            raise SystemExit


if __name__ == '__main__':
    Gen_Tools.setup_logging()
    main(TwitchBot())

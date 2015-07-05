from CommonAssets import GeneralFunctions as Fn
from TwitchBot import TwitchBot


bot = TwitchBot()

if __name__ == '__main__':
    bot.start()
    while True:
        irc_msg = bot.irc_socket.recv(4096).decode("UTF-8").strip('\n\r')
        print(irc_msg)
        if bot.irc_maps.irc_probe[0] in irc_msg:
            s = irc_msg.split(';')
            try:
                user = s[1].strip()[13:]
            except IndexError:
                user = s[5].split(':')[1].split('!')[0]
            bot.command(user, irc_msg, Fn.str_to_bool(s[3][11:]),
                        Fn.str_to_bool(s[5].split(':')[0][10:].replace(' ', '')
                                       if s[5].split(':')[0][10:].replace(' ', '') != ''
                                       else user.lower(), bot.settings.master_access))
        elif bot.irc_maps.irc_probe[1] in irc_msg:
            bot.ping(irc_msg.split()[1])
        elif bot.irc_maps.irc_probe[2] in irc_msg or bot.irc_maps.irc_probe[3] in irc_msg:
            print('###########################[ERROR]###########################\n'
                  '##########[PLEASE VERIFY YOUR OAUTH KEY & BOT NAME]##########\n'
                  '#############################################################\n\n')
            bot.irc_socket.close()
            raise SystemExit

from XMLParser import ParseXML
from CommonAssets import GeneralFunctions as Fn
from glob import glob as get_file
from time import time
from socket import socket


class TwitchBot:
    def __init__(self):
        try:
            self.config_file = get_file('config.xml')[0]
        except IndexError:
            try:
                self.config_file = get_file('*.xml')[0]
            except IndexError:
                print('###########################[ERROR]###########################\n'
                      '###[NO CONFIG OR .XML FILE FOUND IN THE CURRENT DIRECTORY]###\n'
                      '#############################################################\n\n')
                raise SystemExit
        self.irc_socket = socket()
        self.settings = ParseXML.get_settings(self.config_file)
        self.channel = None
        self.user_commands = ParseXML.get_commands(self.config_file)
        self.global_cmd_tracker = {'count': 0, 'last_use': 0.0}

    def connect(self):
        try:
            self.irc_socket.connect((self.settings.host, self.settings.port))
            return True
        except (OSError, TimeoutError):
            print('#########################[ERROR]#########################\n'
                  '###[VERIFY THAT THE SERVER & PORT NUMBERS ARE CORRECT]###\n'
                  '#########################################################\n\n')
            return False

    def authenticate(self):
        self.irc_socket.send(bytes('PASS {0}\r\n'.format(self.settings.oauth), 'UTF-8'))
        self.irc_socket.send(bytes('NICK {0}\r\n'.format(self.settings.bot_name), 'UTF-8'))
        self.irc_socket.send(bytes('USER {0} {0} {0} :{0}\r\n'.format(self.settings.bot_name), 'UTF-8'))
        return True

    def join(self):
        if self.settings.channel[0] != '#':
            self.channel = '#{0}'.format(self.settings.channel)
        self.channel = self.settings.channel.lower()
        self.irc_socket.send(bytes('JOIN {0}\r\n'.format(self.channel), 'UTF-8'))
        self.irc_socket.send(bytes('CAP REQ :twitch.tv/commands\r\n', 'UTF-8'))
        self.irc_socket.send(bytes('CAP REQ :twitch.tv/tags\r\n', 'UTF-8'))
        return True

    def ping(self, response):
        self.irc_socket.send(bytes('PONG :{0}\r\n'.format(response), 'UTF-8'))
        return True

    def message(self, message):
        self.irc_socket.send(bytes('PRIVMSG {0} :{1}\r\n'.format(self.channel, message), 'UTF-8'))
        self.global_cmd_tracker['count'] += 1
        self.global_cmd_tracker['last_use'] = time()
        return True

    def ban(self, u):
        self.message('/ban {0}'.format(u))
        return True

    def unban(self, u):
        self.message('/unban {0}'.format(u))
        return True

    def timeout(self, u, t):
        self.message('/timeout {0} {1}'.format(u, t))
        return True

    def on_cooldown(self, c):
        try:
            return True if (time() - self.user_commands[c]['last_use']) < self.user_commands[c]['cooldown'] else False
        except KeyError:
            return True

    def commands(self, username, message, is_sub, is_mod):
        if (time() - self.global_cmd_tracker['last_use']) > self.settings.command_limit['time_limit']:
            self.global_cmd_tracker['count'] = 0

        if self.global_cmd_tracker['count'] >= self.settings.command_limit['cmd_limit'] \
                and (time() - self.global_cmd_tracker['last_use']) < self.settings.command_limit['time_limit']:
            return  # Do nothing if you've reached the global command rate limit

        cmd = ' '.join(message.split()[4:]).strip().lower()
        if ':!' in cmd:
            if is_mod:
                if ':!ban ' in cmd:
                    name = ''.join(message.split()[5:])
                    self.ban(name)
                    return
                if ':!unban ' in cmd:
                    name = ''.join(message.split()[5:])
                    self.unban(name)
                    return
                if ':!timeout ' in cmd:
                    try:
                        t = int(''.join(message.split()[5:6]))
                        name = ''.join(message.split()[6:])
                    except ValueError:
                        t = 300
                        name = ''.join(message.split()[5:])
                    self.timeout(name, t)
                    return
                if ':!kill {0}'.format(self.settings.bot_name.lower()) in cmd:
                    self.message('Goodbye. MrDestructoid')
                    self.irc_socket.close()
                    raise SystemExit

            if not self.on_cooldown(cmd) and bool(self.user_commands):
                if is_sub and self.user_commands[cmd]['sub_only'] or is_mod:
                    self.message('{0}'.format(self.user_commands[cmd]['response'].replace('${USER}$', username)))
                    self.user_commands[cmd]['last_use'] = time()
                elif not self.user_commands[cmd]['sub_only']:
                    self.message('{0}'.format(self.user_commands[cmd]['response'].replace('${USER}$', username)))
                    self.user_commands[cmd]['last_use'] = time()


bot = TwitchBot()
if bot.connect() and bot.authenticate() and bot.join():
    while True:
        irc_msg = bot.irc_socket.recv(4096).decode("UTF-8").strip('\n\r')
        print(irc_msg)
        if irc_msg.find(' NOTICE * :Login unsuccessful') != -1:
            print('####################[ERROR]####################\n'
                  '###[PLEASE VERIFY YOUR OAUTH KEY & BOT NAME]###\n'
                  '###############################################\n\n')
            raise SystemExit
        if irc_msg.find(' PRIVMSG ') != -1:
            s = irc_msg.split(';')
            try:
                user = s[1].strip()[13:]
            except IndexError:
                user = s[5].split(':')[1].split('!')[0]
            bot.commands(user, irc_msg,
                         Fn.str_to_bool(s[3][11:]),
                         Fn.str_to_bool(s[5].split(':')[0][10:].replace(' ', '')
                                        if s[5].split(':')[0][10:].replace(' ', '') != ''
                                        else user.lower(), bot.settings.master_access))
        if irc_msg.find('PING :') != -1:
            bot.ping(irc_msg.split()[1])

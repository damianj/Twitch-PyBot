import xml.etree.ElementTree as XML_handler
from glob import glob as get_file
from time import time
from socket import socket


class ConnectionSpec(object):
    def __init__(self, host=None, port=6667, oauth=None, bot_name=None, channel=None, command_limit=None):
        self.host = host
        self.port = port
        self.oauth = oauth
        self.bot_name = bot_name
        self.channel = channel
        self.command_limit = command_limit


class ParseXML:
    @staticmethod
    def get_spec(file):
        conn_info = XML_handler.parse(file).getroot().find('general')
        return ConnectionSpec(conn_info.find('server').text,
                              int(conn_info.find('port').text),
                              conn_info.find('oauth').text,
                              conn_info.find('botname').text,
                              conn_info.find('channel').text,
                              {'cmd_limit': int(conn_info.find('commandrate').text.split(':')[0]),
                               'time_limit': float(conn_info.find('commandrate').text.split(':')[1])})

    @staticmethod
    def get_commands(file):
        cmd_dict = {}
        commands = XML_handler.parse(file).getroot().find('commands')
        for cmd in commands.findall('cmd'):
            cmd_dict[cmd.find('trigger').text.lower()] = {'response': cmd.find('response').text,
                                                          'cooldown': float(cmd.find('cooldown').text),
                                                          'last_use': float(cmd.find('cooldown').text)}
        return cmd_dict if cmd_dict != {} else None


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
        self.settings = ParseXML.get_spec(self.config_file)
        self.channel = None
        self.master_commands = [':!ban', ':!unban', ':!timeout', ':!kill {0}'.format(self.settings.bot_name.lower())]
        self.user_commands = ParseXML.get_commands(self.config_file)
        self.global_cmd_info = {'count': 0, 'last_use': 0.0}

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
        self.global_cmd_info['count'] += 1
        self.global_cmd_info['last_use'] = time()
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

    def commands(self, username, message):
        if (time() - self.global_cmd_info['last_use']) > self.settings.command_limit['time_limit']:
            self.global_cmd_info['count'] = 0

        if self.global_cmd_info['count'] >= self.settings.command_limit['cmd_limit'] \
                and (time() - self.global_cmd_info['last_use']) < self.settings.command_limit['time_limit']:
            pass  # Do nothing if you've reached the global command rate limit
        else:
            cmd = ' '.join(message.split()[4:]).strip().lower()
            if any(c in cmd for c in self.master_commands) and username.lower() == self.channel.strip('#'):
                if ':!ban ' in cmd:
                    name = ''.join(message.split()[5:])
                    self.ban(name)
                if ':!unban ' in cmd:
                    name = ''.join(message.split()[5:])
                    self.unban(name)
                if ':!timeout ' in cmd:
                    try:
                        t = int(''.join(message.split()[5:6]))
                        name = ''.join(message.split()[6:])
                    except ValueError:
                        t = 300
                        name = ''.join(message.split()[5:])
                    self.timeout(name, t)
                if ':!kill {0}'.format(self.settings.bot_name.lower()) in cmd:
                    self.message('Goodbye. MrDestructoid')
                    self.irc_socket.close()
                    raise SystemExit
            elif ':!' in cmd:
                if self.user_commands is not None:
                    if cmd in self.user_commands and not self.on_cooldown(cmd):
                        cmd_text = self.user_commands[cmd]['response'].replace('${USER}$', username)
                        self.message('{0}'.format(cmd_text))
                        self.user_commands[cmd]['last_use'] = time()
                    elif self.on_cooldown(cmd):
                        pass  # Optional section to send message when commands are on cooldown
                else:
                    self.message('There are currently no global commands set up.')


varToBool = lambda t: False if t == '0' or any(su in t for su in ['mod', 'global_mod', 'admin', 'staff']) else True

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
                user = s[5].split(' :!')[1]

            subscriber = varToBool(s[3][11:])
            moderator = varToBool(s[5].split(':')[0][10:].replace(' ', ''))
            bot.commands(user, irc_msg)

        if irc_msg.find('PING :') != -1:
            bot.ping(irc_msg.split()[1])

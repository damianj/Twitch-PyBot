import xml.etree.ElementTree as XML_handler
from glob import glob as get_file
from time import time
from socket import socket


class GeneralSettings(object):
    def __init__(self, host=None, port=None, oauth=None, bot_name=None,
                 channel=None, command_limit=None, master_access=None):
        self.host = host
        self.port = port
        self.oauth = oauth
        self.bot_name = bot_name
        self.channel = channel
        self.command_limit = command_limit
        self.master_access = master_access


class ParseXML:
    @staticmethod
    def get_settings(file):
        conn_info = XML_handler.parse(file).getroot().find('general')
        return GeneralSettings(conn_info.find('server').text,
                               int(conn_info.find('port').text),
                               conn_info.find('oauth').text,
                               conn_info.find('botname').text,
                               conn_info.find('channel').text,
                               {'cmd_limit': int(conn_info.find('commandrate').text.split(':')[0]),
                                'time_limit': float(conn_info.find('commandrate').text.split(':')[1])},
                               {'mod': str_to_bool(conn_info.find('modaccess').find('mod').text),
                                'global_mod': str_to_bool(conn_info.find('modaccess').find('global_mod').text),
                                'admin': str_to_bool(conn_info.find('modaccess').find('admin').text),
                                'staff': str_to_bool(conn_info.find('modaccess').find('staff').text)})

    @staticmethod
    def get_commands(file):
        cmd_dict = {}
        commands = XML_handler.parse(file).getroot().find('commands')
        for cmd in commands.findall('cmd'):
            cmd_dict[cmd.find('trigger').text.lower()] = {'response': cmd.find('response').text,
                                                          'cooldown': float(cmd.find('cooldown').text),
                                                          'last_use': float(cmd.find('cooldown').text),
                                                          'sub_only': str_to_bool(cmd.get('sub-only'))}
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
        self.settings = ParseXML.get_settings(self.config_file)
        self.channel = None
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

    def commands(self, username, message, is_sub, is_mod):
        if (time() - self.global_cmd_info['last_use']) > self.settings.command_limit['time_limit']:
            self.global_cmd_info['count'] = 0

        if self.global_cmd_info['count'] >= self.settings.command_limit['cmd_limit'] \
                and (time() - self.global_cmd_info['last_use']) < self.settings.command_limit['time_limit']:
            return  # Do nothing if you've reached the global command rate limit

        cmd = ' '.join(message.split()[4:]).strip().lower()
        if ':!' in cmd:
            if username.lower() == self.channel.strip('#') or is_mod:
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
                if is_sub and self.user_commands[cmd]['sub_only']:
                    self.message('{0}'.format(self.user_commands[cmd]['response'].replace('${USER}$', username)))
                    self.user_commands[cmd]['last_use'] = time()
                elif not self.user_commands[cmd]['sub_only']:
                    self.message('{0}'.format(self.user_commands[cmd]['response'].replace('${USER}$', username)))
                    self.user_commands[cmd]['last_use'] = time()


str_to_bool = lambda x, y = (): True if x.lower() in ('yes', 'true', 't', 'y', '1') or x in y else False

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
            bot.commands(user, irc_msg, str_to_bool(s[3][11:]),
                         str_to_bool(s[5].split(':')[0][10:].replace(' ', ''), bot.settings.master_access))
        if irc_msg.find('PING :') != -1:
            bot.ping(irc_msg.split()[1])

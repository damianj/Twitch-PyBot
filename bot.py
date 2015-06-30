import xml.etree.ElementTree as XML_handler
import socket

class ConnectionSpec(object):
    def __init__(self, host=None, port=6667, oauth=None, bot_name=None, channel=None):
        self.host = host
        self.port = port
        self.oauth = oauth
        self.bot_name = bot_name
        self.channel = channel

class ParseXML:
    @staticmethod
    def get_spec(file):
        conn_info = XML_handler.parse(file).getroot().find('connection')
        return ConnectionSpec(conn_info.find('server').text,
                              int(conn_info.find('port').text),
                              conn_info.find('oauth').text,
                              conn_info.find('botname').text,
                              conn_info.find('channel').text)

    @staticmethod
    def get_commands(file):
        cmd_dict = {}
        commands = XML_handler.parse(file).getroot().find('commands')
        for cmd in commands.findall('cmd'):
            cmd_dict[cmd.find('trigger').text] = cmd.find('response').text
        return cmd_dict if cmd_dict != {} else None

class TwitchBot:
    def __init__(self):
        self.irc_socket = socket.socket()
        self.channel = None
        self.caster_commands = [':!ban', ':!unban', ':!timeout', ':!kill ftw__bot']

    def connect(self, i):
        try:
            self.irc_socket.connect((i.host, i.port))
            return True
        except (OSError, TimeoutError):
            print('Please verify that that server and port numbers are correct.')
            return False

    def authenticate(self, i):
        self.irc_socket.send(bytes('PASS {0}\r\n'.format(i.oauth), 'UTF-8'))
        self.irc_socket.send(bytes('NICK {0}\r\n'.format(i.bot_name), 'UTF-8'))
        self.irc_socket.send(bytes('USER {0} {0} {0} :{0}\r\n'.format(i.bot_name), 'UTF-8'))
        return True

    def join(self, i):
        if i.channel[0] != '#':
            self.channel = '#{0}'.format(i.channel)
        else:
            self.channel = i.channel.lower()
        self.irc_socket.send(bytes('JOIN {0}\r\n'.format(self.channel), 'UTF-8'))
        self.irc_socket.send(bytes('CAP REQ :twitch.tv/commands\r\n', 'UTF-8'))
        self.irc_socket.send(bytes('CAP REQ :twitch.tv/tags\r\n', 'UTF-8'))
        return True

    def ping(self, response):
        self.irc_socket.send(bytes('PONG :{0}\r\n'.format(response), 'UTF-8'))
        return True

    def message(self, message):
        self.irc_socket.send(bytes('PRIVMSG {0} :{1}\r\n'.format(self.channel, message), 'UTF-8'))
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

    def commands(self, username, message):
        cmd = ' '.join(message.split()[4:]).strip()
        if username.lower() == self.channel.strip('#') and any(c in cmd for c in self.caster_commands):
            if ':!ban ' in cmd:
                name = ''.join(message.split()[5:])
                self.ban(name)
            if ':!unban ' in cmd:
                name = ''.join(message.split()[5:])
                self.unban(name)
            if ':!timeout ' in cmd:
                try:
                    time = int(''.join(message.split()[5:6]))
                    name = ''.join(message.split()[6:])
                except ValueError:
                    time = 300
                    name = ''.join(message.split()[5:])
                self.timeout(name, time)
            if ':!kill ftw__bot' in cmd:
                self.message('Goodbye. MrDestructoid')
                self.irc_socket.close()
                raise SystemExit
        elif ':!' in cmd:
            if user_commands is not None:
                if cmd in user_commands:
                    cmd_text = user_commands[cmd].replace('${USER}$', username)
                    self.message('{0}'.format(cmd_text))
                else:
                    self.message('This isn\'t one of the available commands.')
            else:
                self.message('There are currently no global commands set up.')

varToBool = lambda x: False if x == '0' or x != 'mod' else True

settings, user_commands = ParseXML.get_spec('config.xml'), ParseXML.get_commands('config.xml')
bot = TwitchBot()

if bot.connect(settings) and bot.authenticate(settings) and bot.join(settings):
    while True:
        irc_msg = bot.irc_socket.recv(4096).decode("UTF-8").strip('\n\r')
        print(irc_msg)
        if irc_msg.find(' NOTICE * :Login unsuccessful') != -1:
            print('Please verify your oauth key and bot name.\n')
            break
        if irc_msg.find(' PRIVMSG ') != -1:
            s = irc_msg.split(';')
            user = s[1][13:]
            subscriber = varToBool(s[3][11:])
            moderator = varToBool(s[5].split(':')[0][10:].replace(' ', ''))
            bot.commands(user, irc_msg)

        if irc_msg.find('PING :') != -1:
            bot.ping(irc_msg.split()[1])


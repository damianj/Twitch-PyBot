import JSONTools
from CommonAssets import GeneralFunctions as Fn, RestrictedCommands
from glob import glob as get_file
from time import time
from socket import socket


class TwitchBot:
    def __init__(self):
        try:
            self.config_file = get_file('config.json')[0]
        except IndexError:
            self.config_file = get_file('*.json')[0]
        except:
            print('###########################[ERROR]###########################\n'
                  '####[NO CONFIG/.JSON FILE FOUND IN THE CURRENT DIRECTORY]####\n'
                  '#############################################################\n\n')
            raise SystemExit
        self.irc_socket = socket()
        self.settings = JSONTools.ParseJSON.get_settings(self.config_file)
        self.user_commands = JSONTools.ParseJSON.get_commands(self.config_file)
        self.master_commands = RestrictedCommands()
        self.global_cmd_tracker = {'count': 0, 'last_use': 0.0}

    def connect(self):
        try:
            self.irc_socket.connect((self.settings.host, self.settings.port))
            return True
        except (OSError, TimeoutError):
            print('###########################[ERROR]###########################\n'
                  '#####[VERIFY THAT THE SERVER & PORT NUMBERS ARE CORRECT]#####\n'
                  '#############################################################\n\n')
            raise SystemExit

    def authenticate(self):
        self.irc_socket.send(bytes('PASS {0}\r\n'.format(self.settings.oauth), 'UTF-8'))
        self.irc_socket.send(bytes('NICK {0}\r\n'.format(self.settings.bot_name), 'UTF-8'))
        self.irc_socket.send(bytes('USER {0} {0} {0} :{0}\r\n'.format(self.settings.bot_name), 'UTF-8'))
        return True

    def join(self):
        self.irc_socket.send(bytes('CAP REQ :twitch.tv/membership\r\n', 'UTF-8'))
        self.irc_socket.send(bytes('JOIN {0}\r\n'.format(self.settings.channel), 'UTF-8'))
        self.irc_socket.send(bytes('CAP REQ :twitch.tv/commands\r\n', 'UTF-8'))
        self.irc_socket.send(bytes('CAP REQ :twitch.tv/tags\r\n', 'UTF-8'))
        return True

    def ping(self, response):
        self.irc_socket.send(bytes('PONG :{0}\r\n'.format(response), 'UTF-8'))

    def message(self, message):
        self.irc_socket.send(bytes('PRIVMSG {0} :{1}\r\n'.format(self.settings.channel, message), 'UTF-8'))
        self.global_cmd_tracker['count'] += 1
        self.global_cmd_tracker['last_use'] = time()

    def ban(self, u):
        self.message('/ban {0}'.format(u))

    def unban(self, u):
        self.message('/unban {0}'.format(u))

    def timeout(self, u, t):
        self.message('/timeout {0} {1}'.format(u, t))

    def add_cmd(self, c):
        if len(c) != 5:
            self.message('Incorrect syntax: !addcmd|!cmdname|response text|5|False\n'
                         '(number = cooldown for the command, True/False designates sub-only status)')
        elif c[1] in self.user_commands:
            self.message('This command already exists.')
        else:
            try:
                self.user_commands[':{0}'.format(c[1].lower())] = {
                    'response': str(c[2]),
                    'cooldown': float(c[3]),
                    'last_use': float(c[3]),
                    'sub_only': Fn.str_to_bool(c[4])}
                JSONTools.ModifyJSON.add_command(self.config_file, c[1].lower(),
                                                 dict.copy(self.user_commands[':{0}'.format(c[1].lower())]))
            except (KeyError, ValueError):
                self.message('Couldn\'t create the command. Please check the syntax and arguments.')

    def rem_cmd(self, c):
        try:
            if len(c) == 2:
                cmd_name = ':{0}'.format(c[1])
                if cmd_name in self.user_commands:
                    self.user_commands.pop(cmd_name)
                    JSONTools.ModifyJSON.remove_command(self.config_file, cmd_name)
                else:
                    self.message('Command not found. Check spelling and make sure it exists.')
            else:
                raise IndexError
        except IndexError:
            self.message('Incorrect syntax: !remcmd !commandname')

    def on_cooldown(self, c):
        try:
            return True if (time() - self.user_commands[c]['last_use']) < self.user_commands[c]['cooldown'] else False
        except KeyError:
            return True

    def command(self, username, message, is_sub, is_mod):
        if (time() - self.global_cmd_tracker['last_use']) > self.settings.command_limit['time_limit']:
            self.global_cmd_tracker['count'] = 0

        if self.global_cmd_tracker['count'] >= self.settings.command_limit['cmd_limit'] \
                and (time() - self.global_cmd_tracker['last_use']) < self.settings.command_limit['time_limit']:
            return  # Do nothing if you've reached the global command rate limit

        cmd = ' '.join(message.split()[4:]).strip().lower()
        if ':!' in cmd:
            if is_mod and any(c in cmd for c in self.master_commands.cmd_list):
                if ':!addcmd|' in cmd:
                    self.add_cmd(cmd.strip().split('|'))
                elif '!remcmd ' in cmd:
                    self.rem_cmd(cmd.strip().split())
                elif ':!kill {0}'.format(self.settings.bot_name.lower()) in cmd:
                    self.message('Goodbye. MrDestructoid')
                    self.irc_socket.close()
                    raise SystemExit
                elif ':!timeout ' in cmd:
                    try:
                        self.timeout(''.join(message.split()[6:]), int(''.join(message.split()[5:6])))
                    except ValueError:
                        self.timeout(''.join(message.split()[5:]), 300)
                elif ':!ban ' in cmd:
                    self.ban(''.join(message.split()[5:]))
                elif ':!unban ' in cmd:
                    self.unban(''.join(message.split()[5:]))

            elif not self.on_cooldown(cmd) and bool(self.user_commands):
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
        if ' PRIVMSG ' in irc_msg:
            s = irc_msg.split(';')
            try:
                user = s[1].strip()[13:]
            except IndexError:
                user = s[5].split(':')[1].split('!')[0]
            bot.command(user, irc_msg, Fn.str_to_bool(s[3][11:]),
                        Fn.str_to_bool(s[5].split(':')[0][10:].replace(' ', '')
                                       if s[5].split(':')[0][10:].replace(' ', '') != ''
                                       else user.lower(), bot.settings.master_access))
        elif 'PING :' in irc_msg:
            bot.ping(irc_msg.split()[1])
        elif ' NOTICE * :Login unsuccessful' in irc_msg:
            print('###########################[ERROR]###########################\n'
                  '##########[PLEASE VERIFY YOUR OAUTH KEY & BOT NAME]##########\n'
                  '#############################################################\n\n')
            bot.irc_socket.close()
            raise SystemExit

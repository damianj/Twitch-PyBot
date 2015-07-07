import logging
import socket
import glob as get_file
from time import time, timezone, altzone, localtime, daylight
from datetime import datetime, timedelta
from math import ceil as round_up

import JSONTools
from CommonAssets import GeneralFunctions as Gen_Tools, IRCMaps


class TwitchBot:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info('\n\t{0::^50}\n\t{0::^10}[STARTING NEW LOGGING SESSION]{0::^10}\n\t{0::^50}'.format(''))
        try:
            self.config_file = get_file.glob('config.json')[0]
        except IndexError:
            self.logger.error('Could not load the config file. Make sure your '
                              'config.json is in the same directory as TwitchBot.py')
            raise SystemExit
        self.irc_socket = socket.socket()
        self.JSONHandler = JSONTools.JSONHandler()
        self.settings = self.JSONHandler.get_settings(self.config_file)
        self.user_commands = self.JSONHandler.get_commands(self.config_file)
        self.irc_maps = IRCMaps(self.settings.channel)
        self.global_cmd_tracker = {'count': 0, 'last_use': 0.0}

    def start(self):
        self.connect()
        self.authenticate()
        self.join()

    def connect(self):
        try:
            self.irc_socket.connect((self.settings.host, self.settings.port))
            self.logger.info('Connected to {0}:{1} successfully'.format(self.settings.host, self.settings.port))
        except (OSError, TimeoutError):
            self.logger.error('Could not connect using {0}:{1} Please verify the host address '
                              'and port number.'.format(self.settings.host, self.settings.port))
            raise SystemExit

    def authenticate(self):
        self.irc_socket.send(bytes('PASS {0}\r\n'.format(self.settings.oauth), 'UTF-8'))
        self.irc_socket.send(bytes('NICK {0}\r\n'.format(self.settings.bot_name), 'UTF-8'))
        self.irc_socket.send(bytes('USER {0} {0} {0} :{0}\r\n'.format(self.settings.bot_name), 'UTF-8'))
        oauth_halved = self.settings.oauth.replace(self.settings.oauth[int(round_up(
            len(self.settings.oauth)/2.0)):], '*' * int(len(self.settings.oauth)/2.0))
        self.logger.info('Attempting to authenticate bot using:\n'
                         '\tOAUTH: {0}\n\tNICK/USER: {1}'.format(oauth_halved, self.settings.bot_name))

    def join(self):
        self.irc_socket.send(bytes('CAP REQ :twitch.tv/membership\r\n', 'UTF-8'))
        self.irc_socket.send(bytes('JOIN {0}\r\n'.format(self.settings.channel), 'UTF-8'))
        self.irc_socket.send(bytes('CAP REQ :twitch.tv/commands\r\n', 'UTF-8'))
        self.irc_socket.send(bytes('CAP REQ :twitch.tv/tags\r\n', 'UTF-8'))
        self.logger.info('Connected to channel {0} successfully'.format(self.settings.channel))

    def ping(self, response):
        self.irc_socket.send(bytes('PONG :{0}\r\n'.format(response), 'UTF-8'))

    def set_start_time(self, mod):
        self.settings.start_time = datetime.utcnow()
        offset_hrs = -((altzone if daylight and localtime().tm_isdst > 0 else timezone) / 3600)
        offset_min = int((abs(offset_hrs) - abs(int(offset_hrs))) * 60)
        self.logger.info('{0} set the stream start time to {1}'
                         ''.format(mod, str(datetime.now() - timedelta(microseconds=datetime.now().microsecond))))
        return '{0} (UTC:{1}:{2:0^2})'.format(str(datetime.now() - timedelta(microseconds=datetime.now().microsecond)),
                                              int(offset_hrs), offset_min)

    def replace_tags(self, m, u):
        if '${USER}$' in m:
            m = m.replace('${USER}$', u)
        if '${UPTIME}$' in m:
            if self.settings.start_time:
                m = m.replace('${UPTIME}$', str((datetime.utcnow() - self.settings.start_time)
                                                - timedelta(microseconds=(datetime.utcnow()
                                                                          - self.settings.start_time).microseconds)))
            else:
                m = m.replace('${UPTIME}$', '00:00:00')
        return m

    def message(self, message):
        self.irc_socket.send(bytes('PRIVMSG {0} :{1}\r\n'.format(self.settings.channel, message), 'UTF-8'))
        self.global_cmd_tracker['count'] += 1
        self.global_cmd_tracker['last_use'] = time()

    def ban(self, u, mod):
        self.message('/ban {0}'.format(u))
        self.logger.info('{0} banned {1}'.format(mod, u))

    def unban(self, u, mod):
        self.message('/unban {0}'.format(u))
        self.logger.info('{0} un-banned {1}'.format(mod, u))

    def timeout(self, u, t, mod):
        self.message('/timeout {0} {1}'.format(u, t))
        self.logger.info('{0} timed out {1} for {2} second(s)'.format(mod, u, t))

    def add_cmd(self, c, mod):
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
                    'sub_only': Gen_Tools.str_to_bool(c[4])}
                self.JSONHandler.add_command(self.config_file, c[1].lower(),
                                             dict.copy(self.user_commands[':{0}'.format(c[1].lower())]))
                self.logger.info('{0} added the command {1}:{2}'.format(mod, c[1].lower(), c[2].lower()))
            except (KeyError, ValueError):
                self.message('Couldn\'t create the command. Please check the syntax and arguments.')

    def rem_cmd(self, c, mod):
        try:
            if len(c) == 2:
                cmd_name = ':{0}'.format(c[1])
                if cmd_name in self.user_commands:
                    self.user_commands.pop(cmd_name)
                    self.JSONHandler.remove_command(self.config_file, cmd_name)
                    self.logger.info('{0} removed the command {1}'.format(mod, cmd_name))
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
        td = time() - self.global_cmd_tracker['last_use']
        if td > self.settings.command_limit['time_limit']:
            self.global_cmd_tracker['count'] = 0

        if self.global_cmd_tracker['count'] >= self.settings.command_limit['cmd_limit'] \
                and td < self.settings.command_limit['time_limit']:
            self.logger.info('WARNING: {} commands called in {} seconds'.format(self.global_cmd_tracker['count'], td))
            return  # Do nothing if you've reached the global command rate limit

        cmd = ' '.join(message.split()[4:]).strip().lower()
        if ':!' in cmd:
            if is_mod and any(c in cmd for c in self.irc_maps.restricted_commands):
                if ':!addcmd|' in cmd:
                    self.add_cmd(' '.join(message.split()[4:]).strip().split('|'), username)
                elif '!remcmd ' in cmd:
                    self.rem_cmd(cmd.split(), username)
                elif ':!kill {0}'.format(self.settings.bot_name.lower()) in cmd:
                    self.message('Goodbye. MrDestructoid')
                    self.logger.info('{0} killed {1} via the !kill command'.format(username, self.settings.bot_name))
                    self.irc_socket.close()
                    raise SystemExit
                elif ':!timeout ' in cmd:
                    try:
                        self.timeout(''.join(message.split()[6:]), int(''.join(message.split()[5:6])), username)
                    except ValueError:
                        try:
                            self.timeout(''.join(message.split()[5:6]), int(''.join(message.split()[6:])), username)
                        except ValueError:
                            self.timeout(''.join(message.split()[5:]), 300, username)
                elif ':!ban ' in cmd:
                    self.ban(''.join(message.split()[5:]), username)
                elif ':!unban ' in cmd:
                    self.unban(''.join(message.split()[5:]), username)
                elif ':!settime' in cmd:
                    self.message('Updated the stream start time to: {0}'.format(self.set_start_time(username)))

            elif not self.on_cooldown(cmd) and bool(self.user_commands):
                if is_sub and self.user_commands[cmd]['sub_only'] or is_mod:
                    self.message(self.replace_tags('{0}'.format(self.user_commands[cmd]['response']), username))
                    self.user_commands[cmd]['last_use'] = time()
                elif not self.user_commands[cmd]['sub_only']:
                    self.message(self.replace_tags('{0}'.format(self.user_commands[cmd]['response']), username))
                    self.user_commands[cmd]['last_use'] = time()

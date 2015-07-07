import os
import json
import logging.config


class IRCMaps(object):
    def __init__(self, channel):
        self.restricted_commands = (':!ban ', ':!unban ', ':!timeout ',
                                    ':!addcmd|', '!remcmd ', ':!settime', ':!kill ')
        self.irc_probe = (' PRIVMSG {0} :'.format(channel),
                          'PING :tmi.twitch.tv',
                          ':tmi.twitch.tv NOTICE * :Login unsuccessful',
                          ':tmi.twitch.tv NOTICE * :Error logging in')


class BotSettings(object):
    def __init__(self, host=None, port=None, oauth=None, bot_name=None, channel=None,
                 command_limit=None, master_access=None, start_time=None, verbose_logs=None):
        self.host = host
        self.port = port
        self.oauth = oauth
        self.bot_name = bot_name
        self.channel = channel
        self.command_limit = command_limit
        self.master_access = master_access
        self.verbose_logs = verbose_logs
        self.start_time = start_time


class GeneralFunctions:
    @staticmethod
    def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):
        path = default_path
        value = os.getenv(env_key, None)
        if value:
            path = value
        if os.path.exists(path):
            with open(path, 'rt') as f:
                config = json.load(f)
            logging.config.dictConfig(config)
        else:
            logging.basicConfig(level=default_level)

    @staticmethod
    def str_to_bool(s: str, l: iter=()):
        if s.lower() in ('yes', 'true', 't', 'y', '1') or s in l:
            return True
        else:
            return False

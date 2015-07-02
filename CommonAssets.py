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


class GeneralFunctions:
    @staticmethod
    def str_to_bool(s: str, l: iter=()):
        if s.lower() in ('yes', 'true', 't', 'y', '1') or s in l:
            return True
        else:
            return False

    @classmethod
    def process_cmd(cls, l: list):
        try:
            return {'response': str(l[2]), 'cooldown': float(l[3]),
                    'last_use': float(l[3]), 'sub_only': cls.str_to_bool(l[4])}
        except (ValueError, TypeError):
            return False

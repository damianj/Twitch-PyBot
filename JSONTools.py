from urllib import request as url_request, error as url_err
from CommonAssets import BotSettings
from itertools import chain
from datetime import datetime
import logging
import json

class JSONHandler:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def get_settings(self, file):
        with open(file, 'r') as fp:
            settings = json.load(fp)['general']
            self.logger.debug('LOADED SETTINGS:\n{0}\n'.format(settings))
            start_time = self.channel_check(settings['channel'].strip('# ').lower())
            return BotSettings(settings['server'].strip(),
                               settings['port'],
                               settings['oauth'].strip(),
                               settings['botname'].strip(),
                               settings['channel'].strip().lower() if settings['channel'][0].strip().lower() == '#'
                               else '#{0}'.format(settings['channel'].strip().lower()),
                               settings['commandrate'],
                               dict(chain(settings['special_access'].items(),
                                          {settings['channel'].lower().strip('# '): True}.items())),
                               start_time if start_time else None)

    def get_commands(self, file):
        with open(file, 'r') as fp:
            d = json.load(fp)['commands']
            for k in d.keys():
                d[k.lower()] = d.pop(k)
                d[k.lower()].update({'cooldown': float(d[k.lower()]['cooldown'])})
                d[k.lower()].update({'cooldown': float(d[k.lower()]['cooldown'])})
                d[k.lower()].update({'last_use': d[k.lower()]['cooldown']})
            self.logger.debug('LOADED COMMANDS:\n{0}\n'.format(d))
            return d

    def channel_check(self, s: str):
        try:
            url = 'https://api.twitch.tv/kraken/streams/{0}'.format(s.strip('# '))
            data = json.loads(url_request.urlopen(url).read().decode('UTF-8'))
            self.logger.debug('LOADED CHANNEL INFO:\n{0}\n'.format(data))
            return datetime.strptime(data['stream']['created_at'], '%Y-%m-%dT%H:%M:%SZ') if data['stream'] else None
        except (url_err.HTTPError, url_err.URLError, url_err.ContentTooShortError):
            self.logger.error('{0} is not a valid channel. Please verify the name'.format(s.strip('# ')))
            raise SystemExit

    def add_command(self, file, trigger: str, args: dict):
        args.pop('last_use')
        with open(file, 'r') as fp:
            data = json.load(fp)

        data['commands'].update({':{0}'.format(trigger): args})
        with open(file, 'w') as fp:
            json.dump(data, fp)

        self.logger.debug('Edited {0} and added the command {1}'.format(file, trigger))

    def remove_command(self, file, cmd):
        with open(file, 'r') as fp:
            data = json.load(fp)

        data['commands'].pop(cmd)
        with open(file, 'w') as fp:
            json.dump(data, fp)

        self.logger.debug('Edited {0} and removed the command {1}'.format(file, cmd))

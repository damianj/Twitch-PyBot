from urllib import request as url_request, error as url_err
from CommonAssets import GeneralSettings
from itertools import chain
from pprint import PrettyPrinter as pp
import json

class ParseJSON:
    @classmethod
    def get_settings(cls, file):
        with open(file, 'r') as fp:
            settings = json.load(fp)['general']
            print('############################################################\n'
                  '#######################[BOT SETTINGS]#######################\n'
                  '############################################################')
            pp().pprint(settings)
            print('\n')
            cls.channel_check(settings['channel'].strip('# ').lower())
            return GeneralSettings(settings['server'].strip(),
                                   settings['port'],
                                   settings['oauth'].strip(),
                                   settings['botname'].strip(),
                                   settings['channel'].strip().lower()
                                   if settings['channel'][0].strip().lower() == '#'
                                   else '#{0}'.format(settings['channel'].strip().lower()),
                                   settings['commandrate'],
                                   dict(chain(
                                       settings['special_access'].items(),
                                       {settings['channel'].lower().strip('# '): True}.items())))

    @staticmethod
    def get_commands(file):
        with open(file, 'r') as fp:
            d = json.load(fp)['commands']
            for k in d.keys():
                d[k.lower()] = d.pop(k)
                d[k.lower()].update({'cooldown': float(d[k.lower()]['cooldown'])})
                d[k.lower()].update({'cooldown': float(d[k.lower()]['cooldown'])})
                d[k.lower()].update({'last_use': d[k.lower()]['cooldown']})
            print('############################################################\n'
                  '#######################[COMMAND INFO]#######################\n'
                  '############################################################')
            pp().pprint(d)
            print('\n')
            return d

    @staticmethod
    def channel_check(s: str):
        try:
            url = 'https://api.twitch.tv/kraken/channels/{0}'.format(s.strip('# '))
            data = json.loads(url_request.urlopen(url).read().decode('UTF-8'))
            print('############################################################\n'
                  '#######################[CHANNEL INFO]#######################\n'
                  '############################################################')
            pp().pprint(data)
            print('\n')
        except (url_err.HTTPError, url_err.URLError, url_err.ContentTooShortError):
            print('#########################[ERROR]#########################\n'
                  '####[INVALID CHANNEL - PLEASE CHECK THE CHANNEL NAME]####\n'
                  '#########################################################\n\n')
            raise SystemExit


class ModifyJSON:
    @staticmethod
    def add_command(file, trigger: str, args: dict):
        args.pop('last_use')
        with open(file, 'r') as fp:
            data = json.load(fp)

        data['commands'].update({':{0}'.format(trigger): args})
        with open(file, 'w') as fp:
            json.dump(data, fp)

    @staticmethod
    def remove_command(file, cmd):
        with open(file, 'r') as fp:
            data = json.load(fp)

        data['commands'].pop(cmd)
        with open(file, 'w') as fp:
            json.dump(data, fp)

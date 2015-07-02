import json
from CommonAssets import GeneralSettings
from itertools import chain

class ParseJSON:
    @staticmethod
    def get_settings(file):
        with open(file, 'r') as fp:
            settings = json.load(fp)['general']
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
            return d


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

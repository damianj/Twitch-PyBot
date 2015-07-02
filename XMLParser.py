import xml.etree.ElementTree as XML_handler
from CommonAssets import GeneralSettings
from CommonAssets import GeneralFunctions as Fn


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
                               {'mod': Fn.str_to_bool(conn_info.find('modaccess').find('mod').text),
                                'global_mod': Fn.str_to_bool(conn_info.find('modaccess').find('global_mod').text),
                                'admin': Fn.str_to_bool(conn_info.find('modaccess').find('admin').text),
                                'staff': Fn.str_to_bool(conn_info.find('modaccess').find('staff').text),
                                conn_info.find('channel').text.strip('#').lower(): True})

    @staticmethod
    def get_commands(file):
        cmd_dict = {}
        commands = XML_handler.parse(file).getroot().find('commands')
        for cmd in commands.findall('cmd'):
            cmd_dict[cmd.find('trigger').text.lower()] = {'response': cmd.find('response').text,
                                                          'cooldown': float(cmd.find('cooldown').text),
                                                          'last_use': float(cmd.find('cooldown').text),
                                                          'sub_only': Fn.str_to_bool(cmd.get('sub-only'))}
        return cmd_dict if cmd_dict != {} else None

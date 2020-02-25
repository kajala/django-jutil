import re


SFTP_CONNECTION_STRING_REGEX_1 = re.compile(r'^([^@:]+)(:[^@]+)?@([^:]+)(:.+)?')


def parse_sftp_connection(connection: str, exceptions: bool = True) -> (str, str, str, str):  # noqa
    """
    Parses SFTP connection string.
    Connection string format 'USERNAME(:PASSWORD)@HOST(:PATH)' or
    semicolon separated key-value pairs for example 'username=xxx;host=xxx'.
    Returns the match if hostname can be parsed correctly.
    :param connection: str
    :param exceptions: bool
    :return: sftp_user, sftp_password, sftp_host, sftp_path
    """
    username, password, host, remote_path = '', '', '', ''
    m = SFTP_CONNECTION_STRING_REGEX_1.match(connection)
    if m:
        groups = m.groups()
        if len(groups) == 4:
            if m.group(1):
                username = str(m.group(1))
            if m.group(2):
                password = str(m.group(2))[1:]
            if m.group(3):
                host = str(m.group(3))
            if m.group(4):
                remote_path = str(m.group(4))[1:]
    if not host:
        for pair_str in connection.replace(' ', '').split(';'):
            key_value_pair = pair_str.split('=')
            if len(key_value_pair) == 2:
                k, v = key_value_pair
                k = k.lower()
                if k.startswith('sftp_'):
                    k = k[5:]
                if k in ('username', 'user'):
                    username = v
                elif k in ('password', 'passwd', 'pass'):
                    password = v
                elif k in ('host', 'hostname'):
                    host = v
                elif k in ('path', 'remote_path', 'dir'):
                    remote_path = v
    if not host and exceptions:
        raise Exception('Invalid SFTP connection string "{}"'.format(connection))
    return username, password, host, remote_path

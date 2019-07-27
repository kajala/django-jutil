from django.core.management.base import BaseCommand, CommandParser
from jutil.format import format_xml_file


class Command(BaseCommand):
    help = 'Formats XML file'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('filename', type=str)
        parser.add_argument('--encoding', type=str, default='UTF-8')
        parser.add_argument('--xmllint-path', type=str, default='/usr/bin/xmllint')

    def handle(self, **options):
        filename = options['filename']
        encoding = options['encoding']
        xmllint_path = options['xmllint_path']
        print(format_xml_file(filename, encoding=encoding, xmllint_path=xmllint_path).decode())

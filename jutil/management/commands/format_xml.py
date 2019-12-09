from django.core.management.base import BaseCommand, CommandParser
from jutil.format import format_xml_file


class Command(BaseCommand):
    help = 'Formats XML file'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('filename', type=str)
        parser.add_argument('--encoding', type=str, default='UTF-8')

    def handle(self, *args, **options):
        filename = options['filename']
        encoding = options['encoding']
        print(format_xml_file(filename, encoding=encoding).decode())

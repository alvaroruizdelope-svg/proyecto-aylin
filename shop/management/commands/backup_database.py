from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from shop.backups import backup_file
class Command(BaseCommand):
    help='Copia consistente de SQLite mediante su API de backup, nunca dentro del repositorio.'
    def add_arguments(self,parser):parser.add_argument('--output',required=True)
    def handle(self,*args,**options):
        try:backup_file(settings.DATABASES['default']['NAME'],options['output'])
        except Exception as e:raise CommandError('No se pudo crear una copia privada válida; revisa origen/destino.') from e
        self.stdout.write('Copia privada creada y comprobada. No la subas a GitHub.')

import os
import uuid
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from shop.backups import backup_file, safe_path
class Command(BaseCommand):
    help='Restauración LOCAL. Detén primero servidor y worker; crea copia previa antes de sustituir.'
    def add_arguments(self,parser):
        parser.add_argument('--source',required=True)
        parser.add_argument('--confirm-server-stopped',action='store_true')
    def handle(self,*args,**options):
        if not options['confirm_server_stopped']:raise CommandError('Detén servidor y worker y confirma con --confirm-server-stopped.')
        connections.close_all();target=safe_path(settings.DATABASES['default']['NAME']);temp=target.parent/('restore-'+str(uuid.uuid4())+'.sqlite3')
        try:
            backup_file(options['source'],temp)
            if target.exists():backup_file(target,target.parent/('before-restore-'+str(uuid.uuid4())+'.sqlite3'))
            os.replace(temp,target);target.chmod(0o600)
        except Exception as e:raise CommandError('Restauración no completada; conserva copias y revisa el directorio privado.') from e
        self.stdout.write('Base restaurada con copia previa. Reinicia los procesos locales.')

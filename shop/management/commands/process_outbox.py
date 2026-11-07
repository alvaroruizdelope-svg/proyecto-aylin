import time
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from shop.models import Notification
from shop.mail import process_one
class Command(BaseCommand):
    help='Procesa avisos pendientes. No imprime direcciones, cuerpos ni claves.'
    def add_arguments(self,parser): parser.add_argument('--loop',action='store_true')
    def handle(self,*args,**options):
        while True:
            rows=Notification.objects.exclude(status__in=['accepted','needs_reconciliation','recipient_not_allowed','fixture_no_mail']).filter(next_attempt__lte=timezone.now()).values_list('pk',flat=True)[:100]
            counts={}
            for pk in list(rows):
                result=process_one(pk);counts[result]=counts.get(result,0)+1
            self.stdout.write(str(counts))
            if not options['loop']: break
            time.sleep(30)

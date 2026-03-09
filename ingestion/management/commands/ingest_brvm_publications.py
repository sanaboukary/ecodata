from django.core.management.base import BaseCommand
from scripts.connectors.brvm_publications import download_and_store_pdfs

class Command(BaseCommand):
    help = 'Collecte les publications officielles BRVM (PDF) et les stocke.'

    def handle(self, *args, **options):
        download_and_store_pdfs()
        self.stdout.write(self.style.SUCCESS('Collecte des publications BRVM terminée.'))

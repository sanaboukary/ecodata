from django.core.management.base import BaseCommand
from scripts.pipeline import run_ingestion

class Command(BaseCommand):
    help = "Run a one-shot ingestion for a source"

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True, choices=["brvm","worldbank","imf","un","afdb","brvm_publications"])
        parser.add_argument("--indicator")
        parser.add_argument("--date")
        parser.add_argument("--country", default="all")
        parser.add_argument("--dataset")
        parser.add_argument("--key")
        parser.add_argument("--series")
        parser.add_argument("--area")
        parser.add_argument("--time")

    def handle(self, *args, **opts):
        src = opts.pop("source")
        count = run_ingestion(src, **opts)
        self.stdout.write(self.style.SUCCESS(f"{src}: {count} observations upserted"))

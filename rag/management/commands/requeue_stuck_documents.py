from django.core.management.base import BaseCommand
from rag.tasks import requeue_stuck_documents

class Command(BaseCommand):
    help = "Finds documents stuck in processing for more than 10 minutes and retries processing them."

    def handle(self, *args, **options):
        stuck_docs = requeue_stuck_documents()
        self.stdout.write(self.style.SUCCESS(f"Successfully checked and requeued {stuck_docs.count()} stuck documents."))

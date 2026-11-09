import logging

from django.core.management.base import BaseCommand, CommandError

from apps.backups.services import BackupConfigError, run_backup

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Back up the database (local file, optionally Google Drive and/or email)."

    def add_arguments(self, parser):
        parser.add_argument("--no-email", action="store_true", help="Skip email for this run")
        parser.add_argument("--no-drive", action="store_true", help="Skip Google Drive this run")
        parser.add_argument("--local-only", action="store_true", help="Local backup only")
        parser.add_argument("--database", default="default", help="Database alias")

    def handle(self, *args, **options):
        local_only = options["local_only"]
        try:
            report = run_backup(
                options["database"],
                use_email=not (local_only or options["no_email"]),
                use_drive=not (local_only or options["no_drive"]),
            )
        except BackupConfigError as exc:
            raise CommandError(str(exc)) from exc
        for step in report.steps:
            self.stdout.write(step)
        if not report.ok:
            raise CommandError("Backup finished with errors: " + "; ".join(report.errors))
        self.stdout.write(self.style.SUCCESS(f"Backup OK: {report.path}"))

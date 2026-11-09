import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.fixture
def enabled(backup_settings, fake_drive):
    backup_settings.BACKUP_EMAIL_ENABLED = True
    backup_settings.BACKUP_GOOGLE_DRIVE_ENABLED = True
    return backup_settings


def test_command_runs_local_backup(backup_settings, sqlite_db, capsys):
    call_command("backup_db")
    assert "Backup OK" in capsys.readouterr().out


def test_command_no_email_flag(enabled, sqlite_db, mailoutbox, fake_drive):
    call_command("backup_db", "--no-email")
    assert mailoutbox == []
    fake_drive.files.return_value.create.assert_called_once()


def test_command_no_drive_flag(enabled, sqlite_db, mailoutbox, fake_drive):
    call_command("backup_db", "--no-drive")
    assert len(mailoutbox) == 1
    fake_drive.files.assert_not_called()


def test_command_local_only_flag(enabled, sqlite_db, mailoutbox, fake_drive):
    call_command("backup_db", "--local-only")
    assert mailoutbox == []
    fake_drive.files.assert_not_called()


def test_flags_cannot_enable_a_disabled_destination(backup_settings, sqlite_db, mailoutbox):
    call_command("backup_db")  # nothing enabled: no --email flag exists
    assert mailoutbox == []
    with pytest.raises(CommandError):
        call_command("backup_db", "--email")


def test_command_exit_code_on_failure(backup_settings, monkeypatch):
    # in-memory test DB cannot be backed up -> non-zero exit
    with pytest.raises(CommandError, match="Backup finished with errors"):
        call_command("backup_db")


def test_command_missing_setting_is_command_error(backup_settings, sqlite_db):
    backup_settings.BACKUP_EMAIL_ENABLED = True
    backup_settings.EMAIL_HOST = ""
    with pytest.raises(CommandError, match="EMAIL_HOST"):
        call_command("backup_db")
    call_command("backup_db", "--no-email")  # flag turns it off -> no validation needed


def test_database_flag(backup_settings, sqlite_db):
    call_command("backup_db", "--database", "other")

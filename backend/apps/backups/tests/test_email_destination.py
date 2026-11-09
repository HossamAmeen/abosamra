from apps.backups.services import run_backup


def test_email_sent_when_email_flag_enabled(backup_settings, sqlite_db, mailoutbox):
    backup_settings.BACKUP_EMAIL_ENABLED = True
    report = run_backup()
    assert report.ok and len(mailoutbox) == 1
    mail = mailoutbox[0]
    assert mail.to == ["owner@example.com"] and mail.from_email == "noreply@example.com"
    assert mail.subject.startswith("[Test]")
    assert report.path.name in mail.body and "sqlite" in mail.body
    assert len(mail.attachments) == 1 and mail.attachments[0][0] == report.path.name


def test_email_not_sent_when_email_flag_disabled(backup_settings, sqlite_db, mailoutbox):
    run_backup()
    assert mailoutbox == []


def test_large_backup_not_attached(backup_settings, sqlite_db, mailoutbox, monkeypatch):
    backup_settings.BACKUP_EMAIL_ENABLED = True
    backup_settings.BACKUP_EMAIL_MAX_ATTACHMENT_MB = 0  # anything is "too large"
    report = run_backup()
    assert report.ok
    assert mailoutbox[0].attachments == []
    assert "not attached" in mailoutbox[0].body and backup_settings.BACKUP_DIR in mailoutbox[0].body


def test_email_failure_makes_run_fail_but_keeps_file(backup_settings, sqlite_db, monkeypatch):
    backup_settings.BACKUP_EMAIL_ENABLED = True
    monkeypatch.setattr(
        "django.core.mail.EmailMessage.send", lambda self, fail_silently=False: 1 / 0
    )
    report = run_backup()
    assert not report.ok and report.path.exists()
    assert any(e.startswith("email:") for e in report.errors)


def test_alert_never_raises(backup_settings, monkeypatch):
    from apps.backups.destinations import email

    monkeypatch.setattr(
        "django.core.mail.EmailMessage.send", lambda self, fail_silently=False: 1 / 0
    )
    email.send_failure_alert("why", engine="x", host="h")  # must not raise

#!/usr/bin/env python3
import argparse
import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path


DEFAULT_FROM = "sales@exbridge.jp"
DEFAULT_SMTP_HOST = "mail.exbridge.jp"
DEFAULT_SMTP_PORT = 587


def load_env_file(path):
    if not path.exists():
        return
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_env():
    here = Path(__file__).resolve()
    repo = here.parents[1]
    candidates = [
        repo / ".env",
        repo / ".env.local",
        Path("/home/kojima/exdirect/aixec/.env"),
    ]
    for path in candidates:
        load_env_file(path)


def build_message(sender, to, subject, body, reply_to=None):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)
    return msg


def send_message(args):
    load_env()

    sender = args.sender or os.environ.get("SWORK_MAIL_ADDRESS", DEFAULT_FROM)
    username = args.username or os.environ.get("SWORK_SMTP_USER", sender)
    password = args.password or os.environ.get("SWORK_MAIL_PASSWORD") or os.environ.get("FTP_PASS")
    host = args.smtp_host or os.environ.get("SWORK_SMTP_HOST", DEFAULT_SMTP_HOST)
    port = args.smtp_port or int(os.environ.get("SWORK_SMTP_PORT", DEFAULT_SMTP_PORT))

    if not password:
        raise SystemExit("SWORK_MAIL_PASSWORD is not set")

    body = args.body
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    if not body:
        raise SystemExit("--body or --body-file is required")

    msg = build_message(sender, args.to, args.subject, body, args.reply_to)

    if args.dry_run:
        print("dry-run")
        print("smtp:", host, port)
        print("from:", sender)
        print("to:", args.to)
        print("subject:", args.subject)
        print(body)
        return

    if args.ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, timeout=30, context=context) as smtp:
            smtp.login(username, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            if not args.no_starttls:
                context = ssl.create_default_context()
                smtp.starttls(context=context)
                smtp.ehlo()
            smtp.login(username, password)
            smtp.send_message(msg)
    print("sent:", args.to)


def main():
    parser = argparse.ArgumentParser(description="Send SWork outreach/test email.")
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--body-file")
    parser.add_argument("--sender")
    parser.add_argument("--reply-to")
    parser.add_argument("--username")
    parser.add_argument("--password")
    parser.add_argument("--smtp-host")
    parser.add_argument("--smtp-port", type=int)
    parser.add_argument("--ssl", action="store_true")
    parser.add_argument("--no-starttls", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    send_message(args)


if __name__ == "__main__":
    main()


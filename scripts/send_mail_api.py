#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
from urllib import request


DEFAULT_API_URL = "https://aiknowledgecms.exbridge.jp/swork/mail_api.php"


def load_env_file(path):
    if not path.exists():
        return
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def load_env():
    repo = Path(__file__).resolve().parents[1]
    for path in [repo / ".env", repo / ".env.local", Path("/home/kojima/exdirect/aixec/.env")]:
        load_env_file(path)


def main():
    parser = argparse.ArgumentParser(description="Send mail through SWork mail API.")
    parser.add_argument("--to", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--body-file")
    parser.add_argument("--from-address", default="")
    parser.add_argument("--reply-to", default="")
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--token", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env()
    token = args.token or os.environ.get("SWORK_API_TOKEN", "")
    if not token:
        raise SystemExit("SWORK_API_TOKEN is not set")

    body = args.body
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    if not body:
        raise SystemExit("--body or --body-file is required")

    payload = {
        "to": args.to,
        "subject": args.subject,
        "body": body,
        "dry_run": args.dry_run,
    }
    if args.from_address:
        payload["from"] = args.from_address
    if args.reply_to:
        payload["reply_to"] = args.reply_to

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        args.api_url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-SWork-Token": token,
            "User-Agent": "SWork CLI/0.1",
        },
    )
    with request.urlopen(req, timeout=30) as res:
        print(res.read().decode("utf-8"))


if __name__ == "__main__":
    main()

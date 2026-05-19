#!/usr/bin/env python3
import argparse
import csv
import html.parser
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


CONTACT_WORDS = (
    "contact",
    "inquiry",
    "inquiries",
    "otoiawase",
    "toiawase",
    "mailform",
    "form",
    "お問い合わせ",
    "お問合せ",
    "問合せ",
    "お問い合せ",
    "ご相談",
)

COMMON_PATHS = (
    "/contact/",
    "/contact.html",
    "/contact.php",
    "/inquiry/",
    "/inquiry.html",
    "/inquiry.php",
    "/mailform/",
    "/mailform.php",
    "/form/",
    "/otoiawase/",
    "/toiawase/",
)


class PageParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.forms = 0
        self.mailtos = []
        self._a_href = ""
        self._a_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "a":
            self._a_href = attrs.get("href", "")
            self._a_text = []
        elif tag.lower() == "form":
            self.forms += 1

    def handle_data(self, data):
        if self._a_href:
            self._a_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._a_href:
            href = self._a_href.strip()
            text = " ".join(self._a_text).strip()
            if href.lower().startswith("mailto:"):
                self.mailtos.append(href[7:].split("?")[0])
            else:
                self.links.append((href, text))
            self._a_href = ""
            self._a_text = []


def normalize_url(url):
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    parsed = urllib.parse.urlparse(url)
    if not parsed.netloc:
        return ""
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", "", ""))


def fetch(url, timeout=12):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SWork lead research (+https://exbridge.jp/)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as res:
        content_type = res.headers.get("Content-Type", "")
        body = res.read(600_000)
        final_url = res.geturl()
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        return final_url, ""
    encoding = "utf-8"
    match = re.search(r"charset=([\w\-]+)", content_type, re.I)
    if match:
        encoding = match.group(1)
    return final_url, body.decode(encoding, errors="ignore")


def score_link(href, text):
    target = (href + " " + text).lower()
    score = 0
    for word in CONTACT_WORDS:
        if word.lower() in target:
            score += 5
    if href.startswith("#") or href.startswith("javascript:"):
        score -= 10
    if any(x in target for x in ("privacy", "recruit", "sitemap", "access")):
        score -= 3
    return score


def page_has_form(url):
    try:
        final_url, html = fetch(url)
    except Exception:
        return False, url
    parser = PageParser()
    parser.feed(html)
    return parser.forms > 0, final_url


def discover_contact(site_url):
    site_url = normalize_url(site_url)
    if not site_url:
        return "", ""
    try:
        final_url, html = fetch(site_url)
    except Exception as exc:
        return "", "fetch failed: " + str(exc)[:120]

    parser = PageParser()
    parser.feed(html)
    base = final_url or site_url
    candidates = []
    for href, text in parser.links:
        url = urllib.parse.urljoin(base, href)
        if urllib.parse.urlparse(url).netloc != urllib.parse.urlparse(base).netloc:
            continue
        score = score_link(href, text)
        if score > 0:
            candidates.append((score, url))

    root = urllib.parse.urlunparse(urllib.parse.urlparse(base)._replace(path="", params="", query="", fragment=""))
    for path in COMMON_PATHS:
        candidates.append((3, urllib.parse.urljoin(root, path)))

    seen = set()
    ordered = []
    for score, url in sorted(candidates, reverse=True):
        clean = urllib.parse.urlunparse(urllib.parse.urlparse(url)._replace(fragment=""))
        if clean in seen:
            continue
        seen.add(clean)
        ordered.append(clean)

    for url in ordered[:8]:
        ok, final_url = page_has_form(url)
        if ok:
            return final_url, "form found"

    if parser.mailtos:
        return "", "mailto: " + parser.mailtos[0]
    return "", "contact form not found"


def main():
    parser = argparse.ArgumentParser(description="Find contact form URLs for SWork leads.")
    parser.add_argument("--csv", default="data/aikiko_leads.csv")
    parser.add_argument("--out", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--delay", type=float, default=0.2)
    args = parser.parse_args()

    path = Path(args.csv)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    fields = list(rows[0].keys()) if rows else []
    if "contact_form_url" not in fields:
        raise SystemExit("contact_form_url column is required")

    checked = found = 0
    for row in rows:
        if row.get("contact_form_url"):
            continue
        if not row.get("website_url"):
            continue
        if args.limit and checked >= args.limit:
            break
        checked += 1
        form_url, note = discover_contact(row["website_url"])
        if form_url:
            row["contact_form_url"] = form_url
            row["status"] = "form_ready"
            row["next_action"] = "問い合わせフォームから送信準備"
            found += 1
        row["notes"] = (row.get("notes", "") + " / form_search: " + note).strip(" /")
        print(checked, "FOUND" if form_url else "MISS", row.get("company_name", ""), form_url or note)
        time.sleep(args.delay)

    out = Path(args.out) if args.out else path
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print("checked:", checked)
    print("found:", found)
    print("output:", out)


if __name__ == "__main__":
    main()

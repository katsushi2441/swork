#!/usr/bin/env python3
import argparse
import csv
import hashlib
import html.parser
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path


LIST_URL = "http://www.aikiko.or.jp/list.html"
SOURCE_NAME = "愛知県機械工具商業協同組合"
INDUSTRY = "機械工具商社"


class LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href", "")
        if href:
            self.links.append(href)


def clean_text(value):
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = value.replace("&nbsp;", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def fetch_text(url, encoding="cp932"):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "SWork lead research bot/0.1 (+https://exbridge.jp/)"
        },
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read()
    return body.decode(encoding, errors="ignore")


def member_pages(index_url):
    html = fetch_text(index_url)
    parser = LinkParser()
    parser.feed(html)
    urls = []
    for href in parser.links:
        if not href.startswith("list/"):
            continue
        url = urllib.parse.urljoin(index_url, href)
        if url not in urls:
            urls.append(url)
    return urls


def branch_name(html):
    match = re.search(r"<h2>.*?<span[^>]*class=[\"']en[\"'][^>]*>(.*?)</span>", html, re.S | re.I)
    if match:
        return clean_text(match.group(1))
    match = re.search(r"<h2>.*?<span[^>]*class=[\"']ja[\"'][^>]*>(.*?)</span>", html, re.S | re.I)
    return clean_text(match.group(1)) if match else ""


def row_cells(row_html):
    cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row_html, re.S | re.I)
    out = []
    for cell in cells:
        href_match = re.search(r"href=[\"']([^\"']+)[\"']", cell, re.I)
        href = href_match.group(1).strip() if href_match else ""
        text = clean_text(cell)
        out.append((text, href))
    return out


def make_id(company_name, website_url, phone):
    key = "|".join([company_name, website_url, phone])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def parse_member_page(url):
    html = fetch_text(url)
    branch = branch_name(html)
    leads = []
    for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", html, re.S | re.I):
        cells = row_cells(row)
        if len(cells) < 3:
            continue
        company = cells[0][0]
        if not company or "会社名" in company:
            continue
        address = cells[1][0] if len(cells) > 1 else ""
        phone = cells[2][0] if len(cells) > 2 else ""
        website = ""
        if cells[0][1].startswith("http"):
            website = cells[0][1]
        elif len(cells) > 3 and cells[3][1].startswith("http"):
            website = cells[3][1]
        leads.append(
            {
                "id": make_id(company, website, phone),
                "source_url": url,
                "source_name": SOURCE_NAME,
                "company_name": company,
                "branch": branch,
                "website_url": website,
                "email": "",
                "contact_form_url": "",
                "phone": phone,
                "address": address,
                "industry": INDUSTRY,
                "hypothesis": "FAX発注書、見積依頼、型番入力、商品マスタ照合などの手入力削減ニーズがある可能性",
                "status": "new",
                "last_contacted_at": "",
                "next_action": "公式サイトから問い合わせ先を確認",
                "notes": "取得日: " + date.today().isoformat(),
            }
        )
    return leads


def write_csv(path, leads):
    fields = [
        "id",
        "source_url",
        "source_name",
        "company_name",
        "branch",
        "website_url",
        "email",
        "contact_form_url",
        "phone",
        "address",
        "industry",
        "hypothesis",
        "status",
        "last_contacted_at",
        "next_action",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for lead in leads:
            writer.writerow(lead)


def main():
    parser = argparse.ArgumentParser(description="Build SWork leads from Aikiko member pages.")
    parser.add_argument("--url", default=LIST_URL)
    parser.add_argument("--out", default="data/aikiko_leads.csv")
    parser.add_argument("--limit-pages", type=int, default=0)
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    pages = member_pages(args.url)
    if args.limit_pages:
        pages = pages[: args.limit_pages]
    if not pages:
        print("member pages not found", file=sys.stderr)
        return 1

    leads = []
    seen = set()
    for page in pages:
        for lead in parse_member_page(page):
            if lead["id"] in seen:
                continue
            seen.add(lead["id"])
            leads.append(lead)
        time.sleep(args.delay)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_csv(out, leads)
    print("pages:", len(pages))
    print("leads:", len(leads))
    print("output:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


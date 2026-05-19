#!/usr/bin/env python3
import argparse
import csv
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


DEFAULT_NAME = "株式会社エクスブリッジ"
DEFAULT_PERSON = "小島"
DEFAULT_EMAIL = "sales@exbridge.jp"
DEFAULT_PHONE = ""
DEFAULT_ZIP = ""
DEFAULT_PREF = "愛知県"
DEFAULT_ADDRESS = ""
DEFAULT_DEPARTMENT = ""
DEFAULT_POSITION = ""
DEFAULT_WEBSITE = "https://exbridge.jp/"


FIELD_RULES = {
    "company": [
        "会社", "貴社", "法人", "団体", "御社", "company", "organization", "法人名",
    ],
    "name": [
        "氏名", "名前", "お名前", "担当", "ご担当者", "name", "person",
    ],
    "kana": [
        "ふりがな", "フリガナ", "かな", "カナ", "kana", "ruby",
    ],
    "email": [
        "メール", "mail", "email", "e-mail", "アドレス",
    ],
    "phone": [
        "電話", "tel", "phone", "fax",
    ],
    "zip": [
        "郵便", "zip", "postal",
    ],
    "pref": [
        "都道府県", "pref",
    ],
    "address": [
        "住所", "所在地", "address",
    ],
    "department": [
        "部署", "部門", "department",
    ],
    "position": [
        "役職", "position", "title",
    ],
    "website": [
        "url", "website", "ホームページ", "サイト",
    ],
    "subject": [
        "件名", "題名", "subject", "title",
    ],
    "message": [
        "内容", "本文", "問い合わせ", "問合せ", "お問い合わせ", "詳細", "message", "comment", "body",
    ],
}


def normalize(value):
    return re.sub(r"\s+", "", (value or "").lower())


def load_leads(path):
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


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
    load_env_file(repo / ".env")
    load_env_file(repo / ".env.local")


def find_lead(rows, lead_id="", company=""):
    if lead_id:
        for row in rows:
            if row.get("id") == lead_id:
                return row
    if company:
        for row in rows:
            if company in row.get("company_name", ""):
                return row
    return None


def subject_for(_lead):
    return "バイブコーディングによる手入力削減・システム内製化のご提案"


def body_for(lead):
    company = lead.get("company_name", "")
    hypothesis = lead.get("hypothesis", "")
    return (
        f"{company}\nご担当者様\n\n"
        "突然のご連絡失礼いたします。株式会社エクスブリッジです。\n\n"
        "弊社では、バイブコーディングを活用して、FAX発注書、見積依頼、型番入力、商品マスタ照合など、"
        "パソコン上の手入力作業を減らすシステム開発を支援しています。\n\n"
        f"{hypothesis}\n\n"
        "既存SaaSを契約し続ける形ではなく、業務に合わせた仕組みを自社資産として持ち、"
        "社内で育てていけることを重視しています。\n\n"
        "バイブコーディングセミナーとVWorkの導入支援により、外部委託に頼りきらない業務改善・"
        "システム内製化も支援できます。\n\n"
        "もしご関心がありましたら、短時間で現状業務を伺い、どこを自動化できるか整理いたします。\n\n"
        "今後のご案内が不要な場合は、その旨ご返信ください。\n\n"
        "株式会社エクスブリッジ\n"
        "sales@exbridge.jp\n"
        "https://exbridge.jp/"
    )


def values_for(lead):
    return {
        "company": os.environ.get("SWORK_COMPANY_NAME", DEFAULT_NAME),
        "name": os.environ.get("SWORK_CONTACT_NAME", DEFAULT_PERSON),
        "kana": os.environ.get("SWORK_CONTACT_KANA", ""),
        "email": os.environ.get("SWORK_MAIL_ADDRESS", DEFAULT_EMAIL),
        "phone": os.environ.get("SWORK_COMPANY_PHONE", DEFAULT_PHONE),
        "zip": os.environ.get("SWORK_COMPANY_ZIP", DEFAULT_ZIP),
        "pref": os.environ.get("SWORK_COMPANY_PREF", DEFAULT_PREF),
        "address": os.environ.get("SWORK_COMPANY_ADDRESS", DEFAULT_ADDRESS),
        "department": os.environ.get("SWORK_CONTACT_DEPARTMENT", DEFAULT_DEPARTMENT),
        "position": os.environ.get("SWORK_CONTACT_POSITION", DEFAULT_POSITION),
        "website": os.environ.get("SWORK_COMPANY_WEBSITE", DEFAULT_WEBSITE),
        "subject": subject_for(lead),
        "message": body_for(lead),
    }


def element_text(page, handle):
    return handle.evaluate(
        """el => {
            const parts = [];
            const attrs = ['name','id','placeholder','aria-label','title','type'];
            for (const a of attrs) if (el.getAttribute(a)) parts.push(el.getAttribute(a));
            if (el.labels) for (const l of el.labels) parts.push(l.innerText || l.textContent || '');
            let p = el.parentElement;
            for (let i = 0; p && i < 2; i++, p = p.parentElement) parts.push(p.innerText || '');
            return parts.join(' ');
        }"""
    )


def classify(text, tag, input_type):
    text_n = normalize(text)
    if tag == "textarea":
        return "message"
    if any(word in text_n for word in ["ふりがな", "フリガナ", "かな", "カナ", "kana"]):
        return "kana"
    if input_type == "email":
        return "email"
    if input_type in ("tel", "phone"):
        return "phone"
    for field, words in FIELD_RULES.items():
        if any(normalize(w) in text_n for w in words):
            return field
    return ""


def is_skippable(text, input_type):
    text_n = normalize(text)
    if input_type in ("hidden", "submit", "button", "reset", "file", "image", "password"):
        return True
    return any(x in text_n for x in ["captcha", "確認用", "confirmemail", "メール確認"])


def fill_controls(page, values):
    controls = page.query_selector_all("input, textarea")
    filled = []
    used = set()
    for control in controls:
        try:
            if not control.is_visible() or control.is_disabled():
                continue
            tag = control.evaluate("el => el.tagName.toLowerCase()")
            input_type = (control.get_attribute("type") or "text").lower()
            text = element_text(page, control)
            if is_skippable(text, input_type):
                continue
            field = classify(text, tag, input_type)
            if not field or field in used:
                continue
            value = values.get(field, "")
            if value == "":
                continue
            control.fill(value, timeout=3000)
            used.add(field)
            filled.append((field, text[:80]))
        except Exception:
            continue
    return filled


def fill_selects(page, values):
    filled = []
    selects = page.query_selector_all("select")
    for select in selects:
        try:
            if not select.is_visible() or select.is_disabled():
                continue
            text = element_text(page, select)
            field = classify(text, "select", "")
            if field != "pref":
                continue
            pref = values.get("pref", "")
            if not pref:
                continue
            options = select.query_selector_all("option")
            for opt in options:
                label = (opt.inner_text() or "").strip()
                value = opt.get_attribute("value") or ""
                if pref in label or pref == value:
                    select.select_option(value=value, timeout=2000)
                    filled.append(("pref", text[:80]))
                    break
        except Exception:
            continue
    return filled


def choose_radios(page):
    chosen = []
    radios = page.query_selector_all("input[type=radio]")
    for radio in radios:
        try:
            if not radio.is_visible() or radio.is_disabled() or radio.is_checked():
                continue
            text = normalize(element_text(page, radio))
            if any(word in text for word in ["メール", "email", "e-mail", "mail"]):
                radio.check(timeout=2000)
                chosen.append("email")
                break
        except Exception:
            continue
    return chosen


def check_privacy(page):
    checked = []
    boxes = page.query_selector_all("input[type=checkbox]")
    for box in boxes:
        try:
            if not box.is_visible() or box.is_disabled() or box.is_checked():
                continue
            text = element_text(page, box)
            if any(word in normalize(text) for word in ["個人情報", "privacy", "同意", "規約"]):
                box.check(timeout=2000)
                checked.append(text[:80])
        except Exception:
            continue
    return checked


def run(args):
    load_env()
    rows = load_leads(Path(args.csv))
    lead = find_lead(rows, args.lead_id, args.company)
    if not lead:
        raise SystemExit("lead not found")
    form_url = lead.get("contact_form_url", "")
    if not form_url:
        raise SystemExit("contact_form_url is empty")

    values = values_for(lead)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless, slow_mo=args.slow_mo)
        context = browser.new_context(locale="ja-JP", viewport={"width": 1366, "height": 900})
        page = context.new_page()
        page.goto(form_url, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeoutError:
            pass
        filled = fill_controls(page, values)
        filled += fill_selects(page, values)
        radios = choose_radios(page)
        checked = check_privacy(page)
        page.evaluate(
            """() => {
                const buttons = Array.from(document.querySelectorAll('button,input[type=submit],input[type=button]'));
                for (const b of buttons) {
                    const txt = (b.innerText || b.value || '').trim();
                    if (/送信|確認|submit|confirm|send/i.test(txt)) {
                        b.style.outline = '4px solid #f59e0b';
                        b.scrollIntoView({block:'center', inline:'center'});
                        break;
                    }
                }
            }"""
        )
        print("lead:", lead.get("company_name", ""))
        print("url:", form_url)
        print("filled:", ", ".join(field for field, _ in filled) or "none")
        if radios:
            print("selected:", ", ".join(radios))
        if checked:
            print("checked privacy:", len(checked))
        print("status: stopped before submit")
        if args.screenshot:
            page.screenshot(path=args.screenshot, full_page=True)
            print("screenshot:", args.screenshot)
        if not args.headless:
            print("確認して、相手サイト側の送信/確認ボタンだけ人が押してください。")
            page.pause()
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="Open a lead contact form, auto-fill fields, and stop before submit.")
    parser.add_argument("--csv", default="data/aikiko_leads.csv")
    parser.add_argument("--lead-id", default="")
    parser.add_argument("--company", default="")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--slow-mo", type=int, default=100)
    parser.add_argument("--screenshot", default="")
    args = parser.parse_args()
    if not args.lead_id and not args.company:
        raise SystemExit("--lead-id or --company is required")
    run(args)


if __name__ == "__main__":
    main()

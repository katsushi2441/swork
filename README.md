# SWork

SWork は、公開情報をもとに B2B 営業活動を整理し、AIでリード収集、課題仮説、文面作成、送信準備、返信管理まで進めるための営業活動フレームワークです。

## 目的

- 組合名簿などの公開情報から営業候補を整理する
- 会社ごとに課題仮説を作る
- メール文面と問い合わせフォーム文面を作る
- 送信履歴と返信状況を管理する
- 手入力ゼロ化、FAX発注書AI-OCR、VWork導入支援の営業に使う

## 基本方針

- 完全自動大量送信より、半自動で品質を優先する
- 個人メールではなく、会社代表メール・問い合わせフォームを優先する
- 問い合わせフォームは送信ボタンだけ人が確認して押す
- 送信文には配信停止・今後不要の意思表示方法を入れる
- 取得元URL、取得日、送信日、返信状況を残す

## メール設定

送受信アドレス:

```text
sales@exbridge.jp
```

パスワードはMarkdownに保存しない。heteml FTP と同じパスワードを使う場合も、`.env` などGit管理外の環境変数で扱う。

想定する環境変数:

```text
SWORK_MAIL_ADDRESS=sales@exbridge.jp
SWORK_MAIL_PASSWORD=...
SWORK_POP_HOST=pop3.heteml.jp
SWORK_POP_PORT=995
SWORK_POP_USER=sales@exbridge.jp
SWORK_POP_PASSWORD=...
SWORK_SMTP_HOST=smtp.heteml.jp
SWORK_SMTP_PORT=587
SWORK_SMTP_USER=sales@exbridge.jp
```

## 主要ファイル

- `web/index.php` - SWorkターゲット顧客一覧・フォーム自動入力起動
- `web/inbox.php` - sales@exbridge.jp 受信箱
- `web/mail_api.php` - SWorkメール送信API
- `web/.htaccess` - PHPバージョン指定、`.env` / `leads.csv` 直アクセス拒否
- `WORKFLOW.md` - 営業活動の流れ
- `RULES.md` - SWork運用ルール
- `DATA_SCHEMA.md` - リード管理データ項目
- `IMPLEMENTATION.md` - 要件・仕様・実装状況・デプロイ手順
- `templates/outreach-machine-tools.md` - 機械工具商社向け文面
- `prompts/lead-research.md` - リード調査プロンプト
- `prompts/outreach.md` - 営業文面生成プロンプト

## 名簿CSV作成

愛知県機械工具商業協同組合の公開名簿から、営業リストCSVを作成する。

```bash
python3 scripts/build_aikiko_leads.py
```

出力:

```text
data/aikiko_leads.csv
```

## テストメール送信

aiknowledgecms.exbridge.jp のSWorkメールAPI経由:

```bash
python3 scripts/send_mail_api.py \
  --to sales@exbridge.jp \
  --subject "SWork test" \
  --body "SWorkからのテスト送信です。"
```

## 返信メール確認

`sales@exbridge.jp` の受信メールは、aiknowledgecms.exbridge.jp上のSWork Inboxで確認する。

```text
https://aiknowledgecms.exbridge.jp/swork/inbox.php
```

- X共通認証でログインする
- 管理者のみ閲覧できる
- 「POP受信する」で sales@exbridge.jp のPOPメールを取得する
- 取得したメールは `work/swork_inbox/` に保存される

## ターゲット顧客一覧

X共通認証後、営業リストをWebで確認する。

```text
https://aiknowledgecms.exbridge.jp/swork/index.php
```

- ソースは `swork` リポジトリの `web/index.php`
- 公開時は `web/` 配下を `/web/aiknowledgecms_exbridge_jp/swork/` にFTP配置する
- `data/aikiko_leads.csv` を本番 `swork/leads.csv` に配置して表示する
- 標準表示は問い合わせフォームURLがある顧客だけにする
- 会社を選択すると、サイト/問い合わせフォーム、課題仮説、営業文面を表示する
- 問い合わせフォームURL、ステータス、次アクション、メモを保存する
- 入力準備、送信済みを記録する
- 「フォーム自動入力」でローカルPlaywrightを起動し、問い合わせフォームへ自動入力する
- 最後の送信/確認ボタンだけ人が確認して押す

フォーム自動入力を使う前に、ローカルで補助サーバを起動する。

```bash
python3 scripts/form_assistant_server.py
```

SWork画面の「フォーム自動入力」ボタンを押すと、`127.0.0.1:8765` 経由でブラウザを開き、会社名、担当者名、メール、本文などを入力して送信直前で止める。

自社情報は `.env` に設定する。

```text
SWORK_COMPANY_NAME=株式会社エクスブリッジ
SWORK_CONTACT_NAME=
SWORK_CONTACT_KANA=
SWORK_COMPANY_PHONE=
SWORK_COMPANY_ZIP=
SWORK_COMPANY_PREF=愛知県
SWORK_COMPANY_ADDRESS=
SWORK_CONTACT_DEPARTMENT=
SWORK_CONTACT_POSITION=
SWORK_COMPANY_WEBSITE=https://exbridge.jp/
```

問い合わせフォームURLを収集する。

```bash
python3 scripts/find_contact_forms.py
```

2026-05-19時点で、愛知県機械工具商業協同組合リスト324件中154件の問い合わせフォームURLを取得済み。

exbridge.jp の問い合わせフォームと同じ `mail()` 方式:

```bash
php scripts/send_mail_php.php \
  --to sales@exbridge.jp \
  --subject "SWork test" \
  --body "SWorkからのテスト送信です。"
```

SMTP方式:

```bash
python3 scripts/send_mail.py \
  --to sales@exbridge.jp \
  --subject "SWork test" \
  --body "SWorkからのテスト送信です。"
```

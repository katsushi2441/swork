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
SWORK_SMTP_HOST=mail.exbridge.jp
SWORK_SMTP_PORT=587
SWORK_SMTP_USER=sales@exbridge.jp
```

## 主要ファイル

- `WORKFLOW.md` - 営業活動の流れ
- `RULES.md` - SWork運用ルール
- `DATA_SCHEMA.md` - リード管理データ項目
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

# SWork Implementation Notes

Claude/Codex 引き継ぎ用の要件・仕様・実装状況メモ。

## 要件

- SWork は営業活動フレームワーク。
- 公開名簿などから営業リストを作る。
- バイブコーディングセミナー、VWork、手入力ゼロ化、FAX発注書AI-OCRなどをメール・問い合わせフォームで案内する。
- 完全自動大量送信ではなく、半自動で品質を優先する。
- 問い合わせフォームは入力補助まで。最後の送信は人が確認する。
- 送受信メールアドレスは `sales@exbridge.jp`。
- 返信管理をWebで見られるようにする。
- Web認証は URL2AI / AIKnowledgeCMS と同じ X 共通認証を使う。

## ドメイン方針

SWork のWeb機能は `exbridge.jp/swork/` ではなく、次に置く。

```text
https://aiknowledgecms.exbridge.jp/swork/
```

理由:

- `exbridge.jp` と `aiknowledgecms.exbridge.jp` はCookieドメインが違う。
- URL2AI / AIKnowledgeCMS の共通Xログインを使うには、`aiknowledgecms.exbridge.jp` 側に置く方が自然。
- 旧 `https://exbridge.jp/swork/` は削除済み。

## 実装済み

### メール送信API

公開先:

```text
https://aiknowledgecms.exbridge.jp/swork/mail_api.php
```

ローカル実体:

```text
/home/kojima/exdirect/aiknowledgecms/swork/mail_api.php
```

仕様:

- POST専用。
- `X-SWork-Token` または `Authorization: Bearer ...` で認証。
- トークンは `.env` の `SWORK_API_TOKEN`。
- PHPの `mail()` で送信。
- dry-run 対応。
- 送信ログはサーバ側 `work/swork_mail/` に保存。

CLI:

```bash
cd /home/kojima/exdirect/swork
python3 scripts/send_mail_api.py \
  --to sales@exbridge.jp \
  --subject "SWork test" \
  --body "SWorkからのテスト送信です。"
```

dry-run:

```bash
python3 scripts/send_mail_api.py \
  --to sales@exbridge.jp \
  --subject "SWork API dry run" \
  --body "dry run" \
  --dry-run
```

### 受信箱

公開先:

```text
https://aiknowledgecms.exbridge.jp/swork/inbox.php
```

ローカル実体:

```text
/home/kojima/exdirect/aiknowledgecms/swork/inbox.php
```

仕様:

- `aiknowledgecms/auth_common.php` の共通X認証を使う。
- 管理者ユーザーのみ閲覧可能。
- 「POP受信する」で `sales@exbridge.jp` のPOPメールを取得。
- 取得メールはサーバ側 `work/swork_inbox/` にJSON保存。
- POPメールは削除しない。

### ターゲット顧客一覧

公開先:

```text
https://aiknowledgecms.exbridge.jp/swork/index.php
```

ローカル実体:

```text
/home/kojima/exdirect/aiknowledgecms/swork/index.php
```

仕様:

- `aiknowledgecms/auth_common.php` の共通X認証を使う。
- 管理者ユーザーのみ閲覧可能。
- `swork/leads.csv` または `work/swork_leads.csv` を読み込む。
- ターゲット顧客リストを検索・一覧表示する。
- 会社を選択すると、サイト/問い合わせフォーム、課題仮説、営業文面を表示する。
- フォームURLがある場合は画面内iframeと別タブリンクを表示する。
- 画面から問い合わせフォームURL、メール、ステータス、次アクション、メモを保存できる。
- CSV本体は直接書き換えない。上書き情報は `work/swork/lead_overrides.json` に保存する。
- 「入力準備を記録」「送信済みにする」で活動履歴を `work/swork/activities.json` に保存する。
- 会社名、メール、件名、本文をフォーム入力用に個別コピーできる。
- クロスドメイン制限やreCAPTCHAがあるので、最後の送信は人が確認する。

## メールサーバ設定

heteml の設定:

```text
SWORK_POP_HOST=pop3.heteml.jp
SWORK_POP_PORT=995
SWORK_POP_USER=sales@exbridge.jp
SWORK_SMTP_HOST=smtp.heteml.jp
SWORK_SMTP_PORT=587
SWORK_SMTP_USER=sales@exbridge.jp
```

パスワード・APIトークンはMarkdownに書かない。

本番の `.env` 配置:

```text
/web/aiknowledgecms_exbridge_jp/swork/.env
```

ローカルの `.env`:

```text
/home/kojima/exdirect/swork/.env
```

## FTPデプロイ

接続情報は `/home/kojima/exdirect/aixec/.env` の `FTP_HOST` / `FTP_USER` / `FTP_PASS` を使う。

アップロード先:

```text
aiknowledgecms/swork/inbox.php    -> /web/aiknowledgecms_exbridge_jp/swork/inbox.php
aiknowledgecms/swork/mail_api.php -> /web/aiknowledgecms_exbridge_jp/swork/mail_api.php
aiknowledgecms/swork/index.php    -> /web/aiknowledgecms_exbridge_jp/swork/index.php
swork/data/aikiko_leads.csv       -> /web/aiknowledgecms_exbridge_jp/swork/leads.csv
swork/.env                        -> /web/aiknowledgecms_exbridge_jp/swork/.env
aiknowledgecms/swork/.htaccess    -> /web/aiknowledgecms_exbridge_jp/swork/.htaccess
```

`leads.csv` と `.env` は `.htaccess` で直アクセスを拒否する。

旧配置は削除済み:

```text
/web/exbridge_jp/swork/
```

## Gitリポジトリ

SWork:

```text
/home/kojima/exdirect/swork
git@github.com:katsushi2441/swork.git
```

AIKnowledgeCMS:

```text
/home/kojima/exdirect/aiknowledgecms
git@github.com:katsushi2441/aiknowledgecms.git
```

関連コミット:

- `swork`: `cc5c1da Move SWork endpoints to AIKnowledgeCMS domain`
- `aiknowledgecms`: `d4b6ff2 Add SWork endpoints`

## 注意

- `exbridge.jp/swork/` に戻さない。
- パスワードやトークンをコミットしない。
- メール送信は大量自動化しない。
- 問い合わせフォーム送信は最後に人が確認する。
- PHPを編集したらFTP反映まで行う。
- 公開後は `curl` や画面で確認する。

# CordLink

ユーザーの代理としてLinkedInメッセージに自動返信するシステム

## 機能

- LinkedInからのWebhook受信
- GPT-4oによる返信案の自動生成
- Slack Block Kitでの承認UI
- Expandi API経由でのLinkedIn送信
- レートリミット制御（1時間10件まで）

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example`を`.env`にコピーして、各値を設定:

```bash
cp .env.example .env
```

必要な環境変数:
- `OPENAI_API_KEY`: OpenAI APIキー
- `SLACK_BOT_TOKEN`: Slack Bot Token (xoxb-で始まる)
- `SLACK_CHANNEL_ID`: 通知先のSlackチャンネルID
- `EXPANDI_API_KEY`: Expandi APIキー
- `EXPANDI_API_URL`: Expandi APIのベースURL

### 3. Slack Appの設定

1. https://api.slack.com/apps でアプリを作成
2. OAuth & Permissions で以下のスコープを追加:
   - `chat:write`
   - `chat:write.public`
3. Interactivity & Shortcuts を有効化:
   - Request URL: `https://your-domain.com/slack/interactions`
4. Bot Token をコピーして環境変数に設定

### 4. Expandiの設定

1. Expandiダッシュボードで Webhook URL を設定:
   - `https://your-domain.com/webhook/linkedin`
2. 新着メッセージ時にWebhookが送信されるよう設定

### 5. サーバー起動

```bash
python main.py
```

または本番環境では:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## エンドポイント

- `POST /webhook/linkedin` - LinkedInからのWebhook受信
- `POST /slack/interactions` - Slackボタンのインタラクション処理
- `GET /health` - ヘルスチェック

## Webhookペイロード形式

Expandiから以下の形式でデータが送信されることを想定:

```json
{
  "sender_name": "Pasquale Zaccarella",
  "sender_role": "Investor",
  "message": "Well-Vのトラクションについて詳しく聞きたい。",
  "sender_id": "linkedin_user_id_123"
}
```

実際のExpandi APIの仕様に合わせて`main.py`の`linkedin_webhook`関数を調整してください。

## レートリミット

連続送信を防ぐため、1ユーザーあたり1時間に10件までの送信制限を実装しています。
`MAX_MESSAGES_PER_HOUR`の値を変更することで調整可能です。

## デプロイ

本番環境では以下を推奨:
- HTTPS対応（Let's Encrypt等）
- リバースプロキシ（Nginx等）
- プロセス管理（systemd, supervisor等）
- ログ管理
- 環境変数の安全な管理

AWS/GCP/Heroku等へのデプロイも可能です。

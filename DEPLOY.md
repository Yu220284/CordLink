# Render デプロイ手順

## 1. Render にログイン
https://render.com

## 2. 新規 Web Service 作成
- 「New +」→「Web Service」
- GitHub リポジトリを接続（または手動デプロイ）

## 3. 設定
- **Name**: cordlink
- **Environment**: Python 3
- **Build Command**: `./build.sh`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## 4. 環境変数を設定
- `OPENAI_API_KEY`: OpenAI APIキー
- `SLACK_BOT_TOKEN`: Slack Bot Token
- `SLACK_CHANNEL_ID`: Slack Channel ID
- `LINKEDIN_EMAIL`: LinkedIn メールアドレス
- `LINKEDIN_PASSWORD`: LinkedIn パスワード

## 5. デプロイ
- 「Create Web Service」をクリック
- ビルドが完了するまで待つ（5-10分）

## 6. 動作確認
- `https://cordlink.onrender.com/health` にアクセス
- `{"status": "healthy"}` が表示されれば成功

## 7. Slack 設定
- Slack App の Interactivity URL を更新
- `https://cordlink.onrender.com/slack/interactions`

## 完全自動化完成！
- PC を閉じても動作
- 24時間365日稼働
- 完全無料（Render 無料枠）

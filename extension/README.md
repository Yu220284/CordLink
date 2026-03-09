# LinkedIn Auto Reply Chrome Extension

LinkedIn メッセージを自動検知して CordLink に送信する Chrome 拡張機能

## インストール方法

1. **Chrome で拡張機能ページを開く**
   ```
   chrome://extensions/
   ```

2. **デベロッパーモードを有効化**
   - 右上の「デベロッパーモード」をオン

3. **拡張機能を読み込む**
   - 「パッケージ化されていない拡張機能を読み込む」をクリック
   - `/Users/yu/CordLink/extension` フォルダを選択

4. **完了**
   - LinkedIn Auto Reply が表示されれば成功

## 使い方

1. **CordLink を起動**
   ```bash
   cd /Users/yu/CordLink && source .venv/bin/activate
   python3 main.py 8002
   ```

2. **LinkedIn メッセージページを開く**
   ```
   https://www.linkedin.com/messaging/
   ```

3. **自動検知**
   - 新規メッセージが自動的に検知される
   - CordLink に送信される
   - Slack で承認フローが開始

## 動作確認

1. 拡張機能アイコンをクリック
2. 「Test Connection」ボタンをクリック
3. 「✅ Connection OK」が表示されれば成功

## トラブルシューティング

### メッセージが検知されない
- LinkedIn メッセージページを開いているか確認
- コンソールログを確認（F12 → Console）
- 拡張機能を再読み込み

### CordLink に送信されない
- CordLink が起動しているか確認
- `http://localhost:8002/health` にアクセスして確認

## 完全無料で完全自動化

- ✅ LinkedIn メッセージ自動検知
- ✅ AI 返信生成
- ✅ Slack 承認フロー
- ✅ 完全無料（$0/月）

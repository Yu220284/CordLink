from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from openai import OpenAI
import httpx
from collections import defaultdict
from datetime import datetime, timedelta
from config import settings

app = FastAPI()
slack_client = WebClient(token=settings.SLACK_BOT_TOKEN)
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

rate_limiter = defaultdict(list)
MAX_MESSAGES_PER_HOUR = 10

def check_rate_limit(user_id: str) -> bool:
    now = datetime.now()
    hour_ago = now - timedelta(hours=1)
    rate_limiter[user_id] = [ts for ts in rate_limiter[user_id] if ts > hour_ago]
    
    if len(rate_limiter[user_id]) >= MAX_MESSAGES_PER_HOUR:
        return False
    
    rate_limiter[user_id].append(now)
    return True

def generate_reply(sender_name: str, message: str, sender_role: str = "unknown") -> str:
    system_prompt = """あなたはWell-Vの代表・岩瀬として振る舞います。

【基本姿勢】
- 投資家に対しては：率直で透明性のある対応。トラクションや数字を明確に伝え、ミーティングを提案する。
- ユーザーに対しては：親身で丁寧な対応。課題解決を第一に考える。
- 簡潔かつプロフェッショナルに。必要に応じてミーティングリンクを提案。

【返信スタイル】
- 相手の名前で呼びかける
- 具体的な数字や事実を含める（可能な場合）
- 次のアクションを明確にする
- 日本語または英語で、相手のメッセージ言語に合わせる"""

    user_prompt = f"""相手: {sender_name} ({sender_role})
メッセージ: {message}

上記に対する返信を作成してください。"""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content

def send_to_slack(sender_name: str, sender_role: str, original_message: str, ai_reply: str, linkedin_user_id: str):
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🔔 LinkedIn新着メッセージ"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*相手:*\n{sender_name} ({sender_role})"},
                {"type": "mrkdwn", "text": f"*内容:*\n{original_message}"}
            ]
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*🤖 AI作成の返信案:*"}
        },
        {
            "type": "input",
            "block_id": "editable_reply",
            "element": {
                "type": "plain_text_input",
                "action_id": "reply_input",
                "multiline": True,
                "initial_value": ai_reply
            },
            "label": {"type": "plain_text", "text": "返信内容（編集可能）"}
        },
        {
            "type": "actions",
            "block_id": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✅ このまま送信"},
                    "style": "primary",
                    "action_id": "send_original",
                    "value": f"{linkedin_user_id}||{ai_reply}"
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✏️ 修正して送信"},
                    "action_id": "send_edited",
                    "value": linkedin_user_id
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🗑️ 無視"},
                    "style": "danger",
                    "action_id": "ignore",
                    "value": linkedin_user_id
                }
            ]
        }
    ]
    
    slack_client.chat_postMessage(
        channel=settings.SLACK_CHANNEL_ID,
        blocks=blocks,
        text=f"LinkedIn新着メッセージ from {sender_name}"
    )

async def send_to_linkedin(user_id: str, message: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.EXPANDI_API_URL}/messages",
            headers={
                "Authorization": f"Bearer {settings.EXPANDI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={"recipient_id": user_id, "message": message},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()

@app.post("/webhook/linkedin")
async def linkedin_webhook(request: Request):
    payload = await request.json()
    
    sender_name = payload.get("sender_name", "Unknown")
    sender_role = payload.get("sender_role", "unknown")
    message = payload.get("message", "")
    linkedin_user_id = payload.get("sender_id", "")
    
    if not message or not linkedin_user_id:
        raise HTTPException(status_code=400, detail="Invalid payload")
    
    ai_reply = generate_reply(sender_name, message, sender_role)
    send_to_slack(sender_name, sender_role, message, ai_reply, linkedin_user_id)
    
    return JSONResponse({"status": "success"})

@app.post("/slack/interactions")
async def slack_interactions(request: Request):
    form_data = await request.form()
    payload = eval(form_data.get("payload"))
    
    action = payload["actions"][0]
    action_id = action["action_id"]
    user = payload["user"]["username"]
    response_url = payload["response_url"]
    
    if action_id == "send_original":
        value_parts = action["value"].split("||", 1)
        linkedin_user_id = value_parts[0]
        message = value_parts[1]
        
        if not check_rate_limit(linkedin_user_id):
            async with httpx.AsyncClient() as client:
                await client.post(response_url, json={
                    "text": "⚠️ レートリミット超過: 1時間に10件までの送信制限に達しています。",
                    "replace_original": False
                })
            return JSONResponse({"status": "rate_limited"})
        
        await send_to_linkedin(linkedin_user_id, message)
        
        async with httpx.AsyncClient() as client:
            await client.post(response_url, json={
                "text": f"✅ メッセージを送信しました（送信者: {user}）",
                "replace_original": True
            })
    
    elif action_id == "send_edited":
        linkedin_user_id = action["value"]
        edited_message = payload["state"]["values"]["editable_reply"]["reply_input"]["value"]
        
        if not check_rate_limit(linkedin_user_id):
            async with httpx.AsyncClient() as client:
                await client.post(response_url, json={
                    "text": "⚠️ レートリミット超過: 1時間に10件までの送信制限に達しています。",
                    "replace_original": False
                })
            return JSONResponse({"status": "rate_limited"})
        
        await send_to_linkedin(linkedin_user_id, edited_message)
        
        async with httpx.AsyncClient() as client:
            await client.post(response_url, json={
                "text": f"✅ 修正版メッセージを送信しました（送信者: {user}）\n\n送信内容:\n{edited_message}",
                "replace_original": True
            })
    
    elif action_id == "ignore":
        async with httpx.AsyncClient() as client:
            await client.post(response_url, json={
                "text": f"🗑️ メッセージを無視しました（操作者: {user}）",
                "replace_original": True
            })
    
    return JSONResponse({"status": "success"})

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

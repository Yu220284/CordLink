from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slack_sdk import WebClient
from openai import OpenAI
import httpx
from collections import defaultdict
from datetime import datetime, timedelta
from config import settings
import logging
import json
import asyncio
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
slack_client = WebClient(token=settings.SLACK_BOT_TOKEN)
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

rate_limiter = defaultdict(list)
MAX_MESSAGES_PER_HOUR = 10
processed_messages = set()
browser = None
playwright_instance = None

async def get_linkedin_messages():
    global browser, playwright_instance
    try:
        if not browser:
            if not playwright_instance:
                playwright_instance = await async_playwright().start()
            browser = await playwright_instance.chromium.launch(headless=True)
            logger.info("Playwright browser initialized")
        
        page = await browser.new_page()
        await page.goto("https://www.linkedin.com/login", wait_until="networkidle", timeout=30000)
        
        await page.fill("#username", settings.LINKEDIN_EMAIL)
        await page.fill("#password", settings.LINKEDIN_PASSWORD)
        await page.click("button[aria-label='Sign in']")
        await page.wait_for_load_state("networkidle", timeout=30000)
        
        await page.goto("https://www.linkedin.com/messaging/", wait_until="networkidle", timeout=30000)
        
        messages = []
        conversations = await page.query_selector_all("[data-test-id='conversation-item']")
        
        for conv in conversations[:3]:
            try:
                sender_name_elem = await conv.query_selector("[data-test-id='conversation-item-name']")
                sender_text = await sender_name_elem.text_content() if sender_name_elem else "Unknown"
                
                message_elem = await conv.query_selector("[data-test-id='conversation-item-message']")
                message_text = await message_elem.text_content() if message_elem else ""
                
                msg_id = f"{sender_text}_{message_text[:20]}"
                if msg_id not in processed_messages and message_text:
                    messages.append({
                        "sender_name": sender_text,
                        "sender_id": sender_text.replace(" ", "_"),
                        "message": message_text,
                        "timestamp": datetime.now()
                    })
                    processed_messages.add(msg_id)
            except Exception as e:
                logger.error(f"Error processing conversation: {e}")
                continue
        
        await page.close()
        return messages
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return []

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

async def poll_linkedin():
    while True:
        try:
            messages = await get_linkedin_messages()
            for msg in messages:
                sender_name = msg.get("sender_name", "Unknown")
                message = msg.get("message", "")
                linkedin_user_id = msg.get("sender_id", "")
                
                if message and linkedin_user_id:
                    ai_reply = generate_reply(sender_name, message)
                    send_to_slack(sender_name, "LinkedIn User", message, ai_reply, linkedin_user_id)
        except Exception as e:
            logger.error(f"Error in LinkedIn polling: {e}")
        
        await asyncio.sleep(120)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(poll_linkedin())
    logger.info("CordLink started - polling LinkedIn every 2 minutes")

@app.post("/slack/interactions")
async def slack_interactions(request: Request):
    try:
        form_data = await request.form()
        payload_str = form_data.get("payload")
        payload = json.loads(payload_str)
        
        action = payload["actions"][0]
        action_id = action["action_id"]
        user = payload["user"].get("username") or payload["user"].get("name")
        response_url = payload["response_url"]
    except Exception as e:
        logger.error(f"Error parsing Slack payload: {e}")
        return JSONResponse({"text": f"エラーが発生しました: {str(e)}"}, status_code=200)
    
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
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    uvicorn.run(app, host="0.0.0.0", port=port)

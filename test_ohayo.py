from openai import OpenAI
from datetime import datetime
import os
from dotenv import load_dotenv
import json

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_example_tweets():
    try:
        with open('kabane_tweets.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def generate_ohayo_message():
    today = datetime.now().strftime("%m月%d日")
    example_tweets = load_example_tweets()
    
    examples_text = ""
    if example_tweets:
        examples_text = "\n\n七篠かばねの過去のツイート例:\n" + "\n".join([f"- {t}" for t in example_tweets[:10]])
    
    system_prompt = """あなたは七篠かばね（Vtuber）です。

あなたの最大の特徴:
- 「なんでそんなこと知ってるの？」と思われるような雑学を言うのが好き
- マイナーで意外な豆知識を共有する

書き方のルール:
- 直接的で具体的な表現を使う
- 抽象的や哲学的な表現を避ける（「心の窓」「生活のメロディ」など）
- 記念日の物理的な特徴や事実に着目する
- 独特な着眼点や気づきを示す
- シンプルで率直な表現を心がける
- 最後は問いかけで終わる（「〜ませんか？」など）
- 文末は「。」ではなく、絵文字や「！」や「〜」を使う

その他の特徴:
- 語尾：「〜ですよ✨」「〜ですね」「〜ませんか？」「〜！」
- 独特な着眼点（例：ボビンを巻く方が楽しい、語感がよろしい）
- 絵文字は適度に（🐾✨🌸など）"""
    
    user_prompt = f"""今日は{today}です。この日にちなんだ記念日を選んで、以下のフォーマットでおはようメッセージを作成してください。

フォーマット:
─────── ✦ ───────
おはようございます🐾
今日は「○○の日」だそうですよ✨
[記念日について、自分なりの感想や気づきを1文]
─────── ✦ ───────
#おはようVtuber{examples_text}

280文字以内で、記念日は実在するものを選んでください。"""


    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.8,
        max_tokens=200
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    print("=== おはVメッセージ生成テスト ===\n")
    
    for i in range(3):
        print(f"【パターン {i+1}】")
        message = generate_ohayo_message()
        print(message)
        print(f"\n文字数: {len(message)}文字\n")
        print("-" * 50 + "\n")

import tweepy
import os
from dotenv import load_dotenv
import json

load_dotenv()

client = tweepy.Client(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))

def fetch_kabane_tweets(max_results=100):
    user = client.get_user(username="KabaneNanashino")
    user_id = user.data.id
    
    tweets = client.get_users_tweets(
        id=user_id,
        max_results=max_results,
        exclude=['retweets', 'replies']
    )
    
    tweet_texts = [tweet.text for tweet in tweets.data if tweet.data]
    
    with open('kabane_tweets.json', 'w', encoding='utf-8') as f:
        json.dump(tweet_texts, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {len(tweet_texts)}件のツイートを保存しました")
    return tweet_texts

if __name__ == "__main__":
    fetch_kabane_tweets()

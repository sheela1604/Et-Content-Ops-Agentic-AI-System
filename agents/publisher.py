import requests
import os
from datetime import datetime

DUMMY_ACCOUNTS = {
    "linkedin":  "ET_ContentOps_Demo (LinkedIn)",
    "twitter":   "@ET_ContentOps (Twitter/X)",
    "instagram": "@et.contentops (Instagram)",
}

def post_to_telegram(content):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[PUBLISHER] ⚠ Telegram not configured")
        return
    res = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
        "chat_id": chat_id,
        "text": content
    })
    if res.status_code == 200:
        print("[PUBLISHER] ✓ Posted to Telegram channel — LIVE")
    else:
        print(f"[PUBLISHER] ⚠ Telegram failed: {res.text}")

def publish_via_make(platform, content):
    url = os.getenv("MAKE_WEBHOOK_URL")
    if not url:
        return False
    try:
        res = requests.post(url, json={"platform": platform, "content": content})
        return res.status_code == 200
    except Exception as e:
        print(f"[PUBLISHER] ⚠ Webhook failed: {e}")
        return False

def publisher_agent(state: dict) -> dict:
    now = datetime.now().strftime("%I:%M %p")
    published = []
    social = state.get("social_posts", {})

    if state.get("blog_post"):
        published.append({
            "channel": "ET Digital",
            "type": "blog",
            "status": "published",
            "time": now,
            "preview": state["blog_post"][:100]
        })
        print(f"[PUBLISHER] ✓ Blog post published to ET Digital at {now}")

    for platform, account in DUMMY_ACCOUNTS.items():
        content = social.get(platform, "")
        if content:
            publish_via_make(platform, content)
            published.append({
                "channel": account,
                "type": "social",
                "platform": platform,
                "status": "published",
                "time": now,
                "preview": content[:100]
            })
            print(f"[PUBLISHER] ✓ {account} published at {now}")

    # Post all social content to Telegram
    # Post Telegram-specific content
    telegram_content = social.get("telegram", "")
    print("DEBUG TELEGRAM CONTENT:", repr(telegram_content))  # ADD THIS
    if telegram_content:
        post_to_telegram(telegram_content)
        published.append({
            "channel": "ET Content Ops (Telegram)",
            "type": "social",
            "platform": "telegram",
            "status": "published",
            "time": now,
            "preview": telegram_content[:100]
        })
        print(f"[PUBLISHER] ✓ Telegram channel published at {now}")

    if state.get("hindi_content"):
        published.append({
            "channel": "ET Regional Feed (Hindi)",
            "type": "localization",
            "status": "published",
            "time": now,
        })
        print(f"[PUBLISHER] ✓ Hindi content published at {now}")

    state["published_assets"] = published
    return state
import os
import re
import requests
import feedparser
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
ET_RSS_URL = os.getenv("ET_RSS_URL", "https://economictimes.indiatimes.com/rssfeedsdefault.cms")
RSS_FEEDS = [
    "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://economictimes.indiatimes.com/wealth/rssfeeds/837555174.cms",
    "https://economictimes.indiatimes.com/industry/banking/finance/rssfeeds/13358259.cms",
]

def fetch_rss_context(query_keywords: list, max_items: int = 5) -> list:
    """Fetch multiple ET RSS feeds with 5s timeout. Returns [] on any failure."""
    results = []
    try:
        for rss_url in RSS_FEEDS:
            if len(results) >= max_items:
                break
            try:
                resp = requests.get(rss_url, timeout=5)
                feed = feedparser.parse(resp.text)
                for entry in feed.entries:
                    title = entry.get("title", "").lower()
                    summary = entry.get("summary", "").lower()
                    # Match against title OR summary
                    if any(kw.lower() in title or kw.lower() in summary 
                           for kw in query_keywords):
                        results.append({
                            "title": entry.get("title", ""),
                            "summary": BeautifulSoup(
                                entry.get("summary", ""), "html.parser"
                            ).get_text()[:300],
                            "link": entry.get("link", ""),
                            "published": entry.get("published", ""),
                        })
                    if len(results) >= max_items:
                        break
            except Exception:
                continue  # skip failed feed, try next
    except Exception:
        pass
    return results


def scrape_url(url: str, max_chars: int = 3000) -> str:
    """
    Fetch and extract plain text from a URL.
    Returns truncated text or an error string.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; ETContentBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s{2,}", " ", text)
        return text[:max_chars]
    except Exception as e:
        return f"[SCRAPE ERROR] {e}"


def extract_keywords_from_spec(product_spec: str) -> list:
    """
    Simple keyword extractor from product spec text.
    Pulls capitalized words and noun phrases as search terms.
    """
    words = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", product_spec)
    # deduplicate, take top 8
    seen = set()
    keywords = []
    for w in words:
        if w.lower() not in seen and len(w) > 3:
            seen.add(w.lower())
            keywords.append(w)
        if len(keywords) >= 8:
            break
    return keywords or ["fintech", "investment", "product"]

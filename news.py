# news.py

import feedparser
import time

_news_cache = {"data": None, "timestamp": 0}
CACHE_DURATION = 900  # 15 minutes


RSS_FEEDS = {
    "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    "Investing.com Markets": "https://www.investing.com/rss/news.rss",
}


def get_latest_news(limit_per_source=5):
    """RSS feeds se latest financial news headlines fetch karta hai (cached)."""

    now = time.time()
    if _news_cache["data"] and (now - _news_cache["timestamp"]) < CACHE_DURATION:
        return _news_cache["data"]

    all_headlines = []

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries[:limit_per_source]:
                title = entry.get("title", "").strip()
                published = entry.get("published", "")

                if title:
                    all_headlines.append({
                        "source": source_name,
                        "title": title,
                        "published": published
                    })
        except Exception as e:
            print(f"News fetch error for {source_name}: {e}")
            continue

    _news_cache["data"] = all_headlines
    _news_cache["timestamp"] = now

    return all_headlines


def format_news_snapshot():
    """News headlines ko readable text mein format karta hai LLM ke liye."""

    headlines = get_latest_news()

    if not headlines:
        return "Abhi latest news fetch nahi ho payi.\n"

    text = "LATEST FINANCIAL NEWS HEADLINES:\n"

    for item in headlines:
        text += f"- [{item['source']}] {item['title']}\n"

    return text
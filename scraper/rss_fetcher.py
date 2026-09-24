from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re
from urllib.parse import urlsplit, urlunsplit

import feedparser
import requests


RSS_FEEDS = {
    "Google News": "https://news.google.com/rss",
    "BBC": "https://feeds.bbci.co.uk/news/rss.xml",
    "Reuters": "https://feeds.reuters.com/reuters/topNews",
    "NPR": "https://feeds.npr.org/1001/rss.xml",
}


def fetch_news():
    articles = []
    seen_urls = set()

    for source, url in RSS_FEEDS.items():
        try:
            response = requests.get(
                url,
                timeout=15,
                headers={"User-Agent": "NewsPulse/1.0"}
            )
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except Exception as error:
            print(f"Error reading {source} RSS feed: {error}")
            continue

        for entry in feed.entries:
            url_parts = urlsplit(entry.get("link", ""))
            normalized_url = urlunsplit((url_parts.scheme, url_parts.netloc, url_parts.path, url_parts.query, ""))
            if not normalized_url or normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)

            published = entry.get("published") or entry.get("updated") or ""
            try:
                if entry.get("published_parsed"):
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                else:
                    published = parsedate_to_datetime(published).astimezone(timezone.utc).isoformat()
            except (TypeError, ValueError, OverflowError):
                published = datetime.now(timezone.utc).isoformat()

            content_entries = entry.get("content", [])
            content = content_entries[0].get("value", "") if content_entries else ""
            summary = content or entry.get("summary") or entry.get("description") or ""
            summary = re.sub(r"<[^>]+>", " ", unescape(summary)).strip()

            articles.append({
                "title": " ".join(entry.get("title", "").split()),
                "url": normalized_url,
                "source": source,
                "published": published,
                "summary": summary
            })

    return articles


if __name__ == "__main__":
    news = fetch_news()

    print(f"Fetched {len(news)} articles")

    for article in news[:5]:
        print("\nTitle:", article["title"])
        print("Source:", article["source"])
        print("URL:", article["url"])
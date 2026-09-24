import hashlib
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "newspulse")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is required in the project root .env file")

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
)
database = client[MONGODB_DB]
articles_collection = database["articles"]


def create_table():
    articles_collection.create_index("url", unique=True)
    articles_collection.create_index([("cluster", 1), ("published", 1)])
    articles_collection.create_index([("published", -1)])


def article_id(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:20]


def normalize_article(article):
    url = str(article.get("url") or "").strip()
    return {
        "id": article.get("id") or article_id(url),
        "title": str(article.get("title") or ""),
        "url": url,
        "source": str(article.get("source") or ""),
        "published": str(article.get("published") or ""),
        "summary": str(article.get("summary") or ""),
        "content": str(article.get("content") or ""),
        "cluster": article.get("cluster"),
        "cluster_label": str(article.get("cluster_label") or ""),
    }


def save_articles(articles):
    operations = []
    for article in articles:
        normalized = normalize_article(article)
        if not normalized["url"]:
            continue
        operations.append(UpdateOne(
            {"url": normalized["url"]},
            {"$set": normalized},
            upsert=True,
        ))
    if operations:
        articles_collection.bulk_write(operations, ordered=False)


def save_article(article):
    save_articles([article])


def get_articles():
    return list(articles_collection.find({}, {"_id": 0}).sort("id", 1))


if __name__ == "__main__":
    create_table()
    client.admin.command("ping")
    print(f"MongoDB connected: {MONGODB_DB}.articles")

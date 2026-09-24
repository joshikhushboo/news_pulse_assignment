import os
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pymongo import MongoClient, UpdateOne

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "newspulse")
if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is required in the project root .env file")

mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000)
articles_collection = mongo_client[MONGODB_DB]["articles"]
articles_collection.create_index("url", unique=True)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
app = FastAPI(title="NewsPulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def public_article(article):
    result = dict(article)
    result.pop("_id", None)
    return result


def local_summary(article):
    title = str(article.get("title") or "").strip()
    text = re.sub(r"<[^>]+>", "", str(
        article.get("content") or article.get("summary") or ""
    )).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(sentence.strip() for sentence in sentences if sentence.strip())
    if summary:
        return summary[:500]
    if title:
        return f"This article reports on {title}. Read the full story for more details."
    return "A news article is available. Read the full story for more details."


@app.get("/")
def home():
    return {"message": "NewsPulse API is running"}


@app.post("/api/categorize-batch")
def categorize_batch(input_articles: list[dict]):
    keywords = {
        "Sports": ["cricket", "football", "fifa", "ipl", "match", "player", "team", "tennis", "olympic", "sport", "wicket", "runs", "goal", "league"],
        "Technology": ["technology", "tech", "ai", "artificial intelligence", "google", "microsoft", "apple", "amazon", "software", "startup", "iphone", "android", "robot", "cyber", "computer", "internet", "chatgpt", "gemini"],
        "Business": ["business", "market", "stock", "shares", "economy", "company", "bank", "finance", "investment", "profit", "revenue", "ipo", "trade", "industry"],
        "Entertainment": ["movie", "film", "actor", "actress", "bollywood", "hollywood", "music", "singer", "celebrity", "entertainment", "netflix", "series", "cinema"],
        "Science": ["science", "nasa", "space", "research", "scientist", "discovery", "planet", "earth", "moon", "mars", "study", "scientists"],
        "Health": ["health", "hospital", "doctor", "medicine", "disease", "medical", "cancer", "virus", "treatment", "healthcare"],
        "India": ["india", "indian", "delhi", "mumbai", "bengaluru", "bangalore", "kolkata", "chennai", "hyderabad", "modi", "government", "parliament", "rupee"],
        "World": ["world", "international", "global", "america", "usa", "china", "russia", "ukraine", "europe", "uk", "israel", "iran", "united states"],
    }
    results = []
    operations = []

    for input_article in input_articles:
        article_id = input_article.get("id")
        query = {"id": article_id} if article_id is not None else {"url": input_article.get("url", "")}
        cached = articles_collection.find_one(query, {"category": 1})
        category = cached.get("category") if cached and cached.get("category") else None

        if not category:
            text = " ".join(str(input_article.get(field) or "") for field in ("title", "content", "summary")).lower()
            scores = {name: sum(word in text for word in words) for name, words in keywords.items()}
            category = max(scores, key=scores.get) if max(scores.values(), default=0) else "Other"
            operations.append(UpdateOne(query, {"$set": {"category": category}}, upsert=False))

        results.append({"id": article_id, "category": category})

    if operations:
        articles_collection.bulk_write(operations, ordered=False)
    return {"results": results, "gemini_calls": 0}


@app.get("/api/news")
def get_news():
    return [public_article(article) for article in articles_collection.find({}).sort([("published", -1), ("id", -1)])]


@app.get("/api/trending")
def get_trending():
    rows = list(articles_collection.aggregate([
        {"$match": {"cluster": {"$ne": None}}},
        {"$group": {"_id": "$cluster", "article_count": {"$sum": 1}}},
        {"$sort": {"article_count": -1}},
        {"$limit": 5},
    ]))
    trending = []
    for row in rows:
        article = articles_collection.find_one({"cluster": row["_id"]}, sort=[("published", -1), ("id", -1)])
        if article:
            result = public_article(article)
            result["article_count"] = row["article_count"]
            trending.append(result)
    if trending:
        return trending
    return [{**public_article(article), "article_count": 1} for article in articles_collection.find({}).sort([("published", -1), ("id", -1)]).limit(5)]


@app.post("/api/summarize")
def summarize(article: dict):
    fallback = local_summary(article)
    if client:
        try:
            prompt = f"Summarize this news article in two clear sentences. Title: {article.get('title', '')}. Content: {article.get('content') or article.get('summary') or ''}"
            response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=prompt)
            summary = (response.text or "").strip()
            if summary:
                return {"summary": summary, "source": "gemini"}
        except Exception as error:
            print("Gemini summary unavailable; using local summary:", error)
    return {"summary": fallback, "source": "local"}

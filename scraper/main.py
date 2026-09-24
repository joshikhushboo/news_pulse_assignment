from concurrent.futures import ThreadPoolExecutor

from rss_fetcher import fetch_news
from article_extractor import extract_article
from clustering import cluster_articles
from database import client, create_table, get_articles, save_articles


def run_pipeline():
    print("Starting NewsPulse scraper...\n")

    # 1. Fetch news
    print("Fetching news...")
    articles = fetch_news()
    print(f"Fetched {len(articles)} articles.\n")

    if not articles:
        print("No articles found.")
        return

    # Remove duplicate URLs before extraction and clustering.
    articles = list({article["url"]: article for article in articles}.values())

    # 2. Extract article content
    print("Extracting article content...")

    def extract_content(article):
        article["content"] = extract_article(article["url"])
        return article

    with ThreadPoolExecutor(max_workers=8) as executor:
        articles = list(executor.map(extract_content, articles))

    # 3. Cluster similar articles
    print("\nGrouping similar articles...")

    articles = cluster_articles(articles)

    # 4. Save articles
    print("Saving articles to database...")

    save_articles(articles)

    # Recluster the complete stored dataset so old and new rows share one
    # consistent cluster assignment after every rerunnable ingestion.
    all_articles = cluster_articles(get_articles())
    save_articles(all_articles)

    print("\nNewsPulse pipeline completed!")


if __name__ == "__main__":
    try:
        create_table()
        run_pipeline()
    finally:
        client.close()
import math

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


def cluster_articles(articles, num_clusters=5):
    if not articles:
        return []

    texts = [
        " ".join([
            str(article.get("title") or ""),
            str(article.get("summary") or ""),
            str(article.get("content") or "")[:1000],
        ])
        for article in articles
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=5000
    )

    try:
        vectors = vectorizer.fit_transform(texts)
    except ValueError:
        for index, article in enumerate(articles):
            article["cluster"] = 0
            article["cluster_label"] = str(article.get("title") or "Related news").strip()[:90]
        return articles

    # Use fewer clusters for small feeds instead of forcing five groups.
    num_clusters = min(num_clusters, max(1, int(math.sqrt(len(articles)))))
    if num_clusters == 1:
        labels = [0] * len(articles)
    else:
        model = KMeans(
            n_clusters=num_clusters,
            random_state=42,
            n_init=10
        )

        labels = model.fit_predict(vectors)

    labels_by_cluster = {}
    for article, label in zip(articles, labels):
        cluster_id = int(label)
        labels_by_cluster.setdefault(
            cluster_id,
            str(article.get("title") or "").strip()[:90] or f"Cluster {cluster_id + 1}"
        )

    for article, label in zip(articles, labels):
        cluster_id = int(label)
        article["cluster"] = cluster_id
        article["cluster_label"] = labels_by_cluster[cluster_id]

    return articles
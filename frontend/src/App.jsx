import { useEffect, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:3000";

function formatTime(value) {
  if (!value) return "Time unavailable";
  return new Date(value).toLocaleString();
}

function App() {
  const [timeline, setTimeline] = useState({ clusters: [], sources: [] });
  const [latestArticles, setLatestArticles] = useState([]);
  const [selectedSource, setSelectedSource] = useState("All");
  const [selectedCluster, setSelectedCluster] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const loadTimeline = async (source = selectedSource) => {
    const query = source !== "All" ? `?source=${encodeURIComponent(source)}` : "";
    const response = await fetch(`${API_URL}/timeline${query}`);
    if (!response.ok) throw new Error("Timeline request failed");
    const data = await response.json();
    setTimeline(data);
    setSelectedCluster((current) => (
      current ? data.clusters.find((cluster) => cluster.id === current.id) || null : null
    ));
  };

  const loadLatest = async () => {
    const response = await fetch(`${API_URL}/articles/latest`);
    if (!response.ok) throw new Error("Latest articles request failed");
    setLatestArticles(await response.json());
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const [timelineResponse, latestResponse] = await Promise.all([
          fetch(`${API_URL}/timeline`),
          fetch(`${API_URL}/articles/latest`),
        ]);
        if (!timelineResponse.ok || !latestResponse.ok) throw new Error("News data request failed");
        setTimeline(await timelineResponse.json());
        setLatestArticles(await latestResponse.json());
      } catch (loadError) {
        setError(loadError.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const refreshData = async () => {
    setRefreshing(true);
    setError("");
    try {
      const triggerResponse = await fetch(`${API_URL}/ingest/trigger`, { method: "POST" });
      if (!triggerResponse.ok) throw new Error("Could not start ingest job");
      const job = await triggerResponse.json();
      let status = "running";

      while (status === "running") {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        const statusResponse = await fetch(`${API_URL}/ingest/status/${job.jobId}`);
        const statusData = await statusResponse.json();
        status = statusData.status;
        if (status === "failed") throw new Error("Ingest job failed");
      }

      await loadTimeline();
      await loadLatest();
    } catch (refreshError) {
      setError(refreshError.message);
    } finally {
      setRefreshing(false);
    }
  };

  const openCluster = async (cluster) => {
    const response = await fetch(`${API_URL}/clusters/${cluster.id}`);
    if (response.ok) setSelectedCluster(await response.json());
  };

  const visibleLatestArticles = selectedSource === "All"
    ? latestArticles
    : latestArticles.filter((article) => article.source === selectedSource);

  return (
    <div className="app">
      <header className="navbar">
        <h1>NewsPulse</h1>
        <nav>
          <a href="#timeline">Timeline</a>
          <a href="#news">Latest</a>
          <button className="refresh-button" onClick={refreshData} disabled={refreshing}>
            {refreshing ? "Refreshing..." : "Refresh Data"}
          </button>
        </nav>
      </header>

      <main>
        <section className="hero">
          <p className="tagline">YOUR DAILY NEWS PULSE</p>
          <h2>Stay informed.<br />Stay ahead.</h2>
          <p>Discover related stories across sources on one clear timeline.</p>
        </section>

        <section className="timeline-section" id="timeline">
          <div className="section-header">
            <div>
              <p className="section-label">STORY CLUSTERS</p>
              <h2>News Timeline</h2>
            </div>
          </div>

          <div className="timeline-toolbar">
            <p className="section-description">
              Follow the stories gaining momentum across the news cycle.
            </p>
            <label className="source-select">
              <span>Filter source</span>
              <select value={selectedSource} onChange={(event) => {
                const source = event.target.value;
                setSelectedSource(source);
                loadTimeline(source).catch((loadError) => setError(loadError.message));
              }}>
                <option value="All">All sources</option>
                {timeline.sources.map((source) => <option key={source} value={source}>{source}</option>)}
              </select>
            </label>
          </div>

          {error && <p className="status">{error}</p>}
          {loading ? <p className="status">Loading timeline...</p> : (
            <div className="timeline-track">
              {timeline.clusters.map((cluster) => (
                <button
                  className="timeline-cluster"
                  key={cluster.id}
                  style={{ "--intensity": cluster.intensity || cluster.articleCount || 1 }}
                  onClick={() => openCluster(cluster)}
                >
                  <span className="timeline-dot" />
                  <span className="timeline-date">{formatTime(cluster.startTime)}</span>
                  <strong>{cluster.label}</strong>
                  <span className="timeline-count">{cluster.articleCount} articles</span>
                  <small>Through {formatTime(cluster.endTime)}</small>
                </button>
              ))}
              {!timeline.clusters.length && <p className="status">No clustered articles found.</p>}
            </div>
          )}
        </section>

        {selectedCluster && (
          <section className="cluster-detail">
            <div className="section-header">
              <div>
                <p className="section-label">SELECTED CLUSTER</p>
                <h2>{selectedCluster.label}</h2>
              </div>
              <button onClick={() => setSelectedCluster(null)}>Close</button>
            </div>
            <div className="cluster-articles">
              {selectedCluster.articles.map((article) => (
                <article className="cluster-article" key={article.id}>
                  <h3>{article.title}</h3>
                  <p>{article.source} · {formatTime(article.published)}</p>
                  <a href={article.url} target="_blank" rel="noopener noreferrer">Read original article →</a>
                </article>
              ))}
            </div>
          </section>
        )}

        <section className="news-section" id="news">
          <div className="section-header">
            <div>
              <p className="section-label">LATEST STORIES</p>
              <h2>Latest News</h2>
            </div>
          </div>
          <div className="latest-grid">
            {visibleLatestArticles.map((article) => (
              <article className="latest-article" key={article.id}>
                <h3>{article.title}</h3>
                <p className="latest-meta">{article.source} · {formatTime(article.published)}</p>
                <p>{article.summary ? article.summary.replace(/<[^>]*>/g, "").slice(0, 180) : "Full article content is available at the original source."}</p>
                <a href={article.url} target="_blank" rel="noopener noreferrer">Read original article →</a>
              </article>
            ))}
            {!visibleLatestArticles.length && <p className="status">No latest articles found for this source.</p>}
          </div>
        </section>
      </main>

      <footer className="footer">
        <div>
          <strong>NewsPulse</strong>
          <p>Topic-clustered news from multiple sources.</p>
        </div>
        <small>Built with Python, Node.js, React and SQLite.</small>
      </footer>
    </div>
  );
}

export default App;

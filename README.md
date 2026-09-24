# NewsPulse: Topic-Clustered News Timeline

NewsPulse is a full-stack news ingestion and exploration app. It reuses the existing Python RSS scraper, article extraction, TF-IDF clustering, and React UI. Python and Node.js now share MongoDB Atlas through the `MONGODB_URI` environment variable.

## Architecture

- `scraper/`: RSS fetching, normalization, article-page extraction, TF-IDF/KMeans grouping, and MongoDB persistence.
- `backend-node/`: Express API, MongoDB access, and Python subprocess job management.
- `backend/`: existing FastAPI category, trending, and optional Gemini/local summary compatibility service, also backed by MongoDB.
- `frontend/`: React timeline, cluster explorer, source filter, latest articles, and refresh workflow.

## Run Locally

Create a root `.env` from `.env.example` and set `MONGODB_URI` to your MongoDB Atlas connection string. Never commit `.env` or include the password in source code.

Terminal 1, FastAPI summary/category service:

```powershell
cd backend
uvicorn main:app --reload --port 8000
```

Terminal 2, required Node API:

```powershell
cd backend-node
npm install
npm start
```

Terminal 3, React frontend:

```powershell
cd frontend
npm install
npm run dev
```

The frontend uses `http://127.0.0.1:3000` for the Node API and `http://127.0.0.1:8000` for the optional existing FastAPI service. Override them for deployment with:

```env
VITE_API_URL=https://your-node-api.example.com
VITE_NEWS_API_URL=https://your-fastapi.example.com
```

## Required API

- `GET /clusters`
- `GET /clusters/:id`
- `GET /timeline?source=BBC`
- `POST /ingest/trigger`
- `GET /ingest/status/:jobId`
- `GET /articles/latest`

`POST /ingest/trigger` starts the existing Python scraper. The React Refresh Data button polls its status and reloads the timeline when the job completes. The Python subprocess inherits `MONGODB_URI` and writes to the same Atlas collection.

## Python Ingestion

The scraper reads these public RSS feeds:

- Google News: `https://news.google.com/rss`
- BBC: `https://feeds.bbci.co.uk/news/rss.xml`
- Reuters: `https://feeds.reuters.com/reuters/topNews`
- NPR: `https://feeds.npr.org/1001/rss.xml`

RSS entries are normalized into `title`, `url`, `source`, `published`, and `summary`. The fetcher accepts `content`, `summary`, and `description` fields, supports feed-provided parsed dates and RFC dates, and uses the current UTC time as a safe fallback when a date is missing or invalid.

Each article URL is normalized and unique. The database uses `url` as a unique key and upserts existing rows, so repeated ingestion does not create duplicates. The pipeline calls `extract_article(url)` for every article, stores the extracted page body in `content`, and retains the RSS summary when extraction fails.

Topic grouping uses local TF-IDF plus deterministic KMeans (`stop_words="english"`, `max_features=5000`, `random_state=42`, `n_init=10`). The number of groups is `min(5, floor(sqrt(article_count)))`, with one group for small feeds. Labels come from the first representative headline in each persisted cluster, not from the internal numeric cluster ID. This avoids using Gemini for core clustering.

Known limitation: KMeans is not semantic understanding, so stories with different wording may be separated and similarly worded stories can be grouped together. Cluster IDs can change when the feed contents change, while labels remain stable for the current stored dataset.

After saving a feed batch, the pipeline reclusters the complete persisted dataset so existing and newly fetched articles share one consistent assignment.

## MongoDB Schema

MongoDB database `newspulse` uses the `articles` collection. Each document stores `id`, unique `url`, `title`, `source`, normalized `published`, RSS `summary`, extracted `content`, numeric internal `cluster`, human-readable `cluster_label`, and optional `category`. The Python and Node applications create a unique `url` index and supporting cluster/time indexes.

The old `scraper/newspulse.db` file is retained as a local backup. To migrate its existing rows once:

```powershell
cd scraper
python migrate_sqlite_to_mongodb.py
```

## Environment Variables

Both Node and Python use the root `.env` file. See [.env.example](.env.example):

- `MONGODB_URI`: MongoDB Atlas connection string.
- `MONGODB_DB`: optional database name, defaults to `newspulse`.
- `PORT`: public Node port.
- `PYTHON_COMMAND`: Python executable available to the Node service.

Frontend build variables:

- `VITE_API_URL`: public Node API URL.
- `VITE_NEWS_API_URL`: public FastAPI URL if the optional category/summary features are enabled.

Keep `.env` files and API keys out of source control. Gemini is optional and is not used for clustering.

## Deployment

Deploy `backend-node` as a Node service with the repository root and `scraper/` available. Install Node dependencies, install `scraper/requirements.txt` into the service Python environment, and set `MONGODB_URI` and `MONGODB_DB`. The Node service must run on a host that permits Python subprocesses. If the host does not, run the Python scraper as a scheduled/separate worker using the same `MONGODB_URI` and keep `/ingest/trigger` disabled or routed to that worker.

Deploy `frontend` as a static Vite site with `VITE_API_URL` set to the public Node URL. Optional FastAPI features use `VITE_NEWS_API_URL`.

Live frontend URL: `<add deployed frontend URL>`

Live backend URL: `<add deployed Node API URL>`

MongoDB Atlas provides the production persistence. Keep `newspulse.db` only as a local migration backup. The active Python, Node, and FastAPI code no longer reads SQLite.

## Video Walkthrough Script

1. Show the RSS scraper and the MongoDB `articles` collection, pointing out source, published timestamp, cluster, and cluster label.
2. Open the React app and show the timeline clusters across the time axis.
3. Change the source filter and explain that the timeline reloads from `GET /timeline?source=...`.
4. Click a cluster and show its headlines, sources, publication times, and original links.
5. Click Refresh Data, show the ingest request and polling state, then show the refreshed timeline.
6. Briefly show the five Node endpoints and explain that Node reads MongoDB Atlas while triggering the existing Python scraper for ingestion.

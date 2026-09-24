# 📰 News Pulse — Topic-Clustered News Timeline

News Pulse is a full-stack news aggregation application that collects live articles from multiple RSS feeds, extracts article content, groups related stories into topic clusters, and visualizes them on a chronological timeline.

## 🚀 Live Demo

**Frontend:** https://frontend-theta-vert-69.vercel.app/

**Backend API:** https://news-pulse-assignment.onrender.com/

## ✨ Features

* Fetches news from multiple public RSS feeds
* Normalizes inconsistent RSS data
* Removes duplicate articles
* Extracts the main article content from original webpages
* Groups related articles using TF-IDF + K-Means clustering
* Displays topic clusters on a visual timeline
* Shows earliest and latest article timestamps
* Cluster detail view with:

  * Headline
  * Source
  * Published time
  * Original article link
* Filter articles by source
* Refresh Data button to trigger a new ingestion job
* Ingestion status polling
* Responsive React UI

## 🏗️ Architecture

```text
                 RSS Feeds
                     │
                     ▼
            Python Scraper
          ┌─────────────────┐
          │ RSS Ingestion   │
          │ Article Extract │
          │ TF-IDF + KMeans │
          └────────┬────────┘
                   │
                   ▼
              MongoDB Atlas
                   │
                   ▼
          Node.js / Express
                   │
                   ▼
            React / Vite UI
                   │
                   ▼
          Topic Timeline + UI
```

## 🛠️ Tech Stack

### Frontend

* React
* Vite
* JavaScript
* CSS

### Backend

* Node.js
* Express.js
* REST APIs

### Data & Processing

* Python
* Feedparser
* Requests
* BeautifulSoup
* Scikit-learn
* MongoDB Atlas

### Deployment

* Vercel — Frontend
* Render — Backend
* MongoDB Atlas — Database

## 📰 RSS Sources

The application uses multiple public RSS feeds, including:

* Google News RSS
* BBC News RSS
* Reuters RSS

The feeds are processed through the Python ingestion pipeline.

## 🧠 Topic Grouping Approach

News articles are grouped using **TF-IDF vectorization and K-Means clustering**.

### Process

1. Article titles and extracted content are collected.
2. Text is cleaned and normalized.
3. TF-IDF converts article text into numerical vectors.
4. K-Means groups articles with similar textual characteristics.
5. Each article receives a cluster ID and cluster label.
6. The frontend uses these clusters to create the timeline.

### Current Configuration

* TF-IDF English stop-word removal
* Maximum 5,000 features
* K-Means clustering
* Fixed maximum of 5 clusters
* `random_state=42`
* `n_init=10`

### Limitation

The current clustering approach uses a fixed number of K-Means clusters. With more time, the number of clusters could be determined dynamically using methods such as silhouette analysis, or semantic embeddings could be used to improve topic similarity across different wording and sources.

## 🔄 Article Processing

For each RSS entry, News Pulse:

1. Reads the RSS metadata.
2. Normalizes the article URL.
3. Handles missing publication dates using available feed timestamps.
4. Removes duplicate URLs.
5. Fetches the original article webpage.
6. Extracts paragraph text from the page.
7. Stores the normalized article and extracted content in MongoDB.

If article extraction fails, the pipeline handles the failure gracefully instead of stopping the entire ingestion process.

## 🔌 API Endpoints

### Get Clusters

```http
GET /clusters
```

Returns cluster labels, article counts, and earliest/latest timestamps.

### Get Cluster Details

```http
GET /clusters/:id
```

Returns articles belonging to a cluster, sorted chronologically.

### Get Timeline

```http
GET /timeline
```

Returns timeline-friendly cluster data including:

* Cluster label
* Start time
* End time
* Article count
* Intensity/size information

### Trigger Ingestion

```http
POST /ingest/trigger
```

Starts the Python ingestion pipeline and returns a job ID.

### Check Ingestion Status

```http
GET /ingest/status/:jobId
```

Returns the current ingestion job status.

## 🔐 Environment Variables

Create a `.env` file where required.

```env
MONGODB_URI=your_mongodb_connection_string
PORT=3000
```

For the Vite frontend:

```env
VITE_API_URL=http://127.0.0.1:3000
```

For production, the frontend uses the deployed Render backend URL.

**Environment files containing secrets are not committed to GitHub.**

## 💻 Run Locally

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd news-pulse
```

### 2. Install backend dependencies

```bash
cd backend-node
npm install
```

### 3. Install Python dependencies

```bash
cd ../scraper
pip install -r requirements.txt
```

### 4. Configure environment variables

Add your MongoDB connection string to `.env`.

### 5. Start Node backend

```bash
cd ../backend-node
node server.js
```

The API runs on:

```text
http://localhost:3000
```

### 6. Start frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available through the Vite development server.

## 📁 Project Structure

```text
news-pulse/
│
├── scraper/
│   ├── RSS ingestion
│   ├── article extraction
│   ├── topic clustering
│   └── Python dependencies
│
├── backend-node/
│   ├── server.js
│   ├── package.json
│   └── package-lock.json
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── .env.example
├── .gitignore
└── README.md
```

## 🌐 Deployment

### Frontend

The React/Vite frontend is deployed on **Vercel**.

Live application:

https://frontend-theta-vert-69.vercel.app/

### Backend

The Node.js/Express backend is deployed on **Render**.

API:

https://news-pulse-assignment.onrender.com/

### Database

MongoDB Atlas is used as the persistent database.

The Python scraper handles ingestion and processing, MongoDB stores the articles and cluster information, and the Node.js backend exposes the data through REST APIs.

## 🔁 Refresh Data Flow

When the user clicks **Refresh Data**:

```text
React Frontend
      │
      ▼
POST /ingest/trigger
      │
      ▼
Node.js Backend
      │
      ▼
Python Ingestion Pipeline
      │
      ▼
MongoDB Atlas
      │
      ▼
Frontend polls /ingest/status/:jobId
      │
      ▼
Timeline refreshes
```

## 🎯 Assignment Requirements Covered

* [x] Multiple RSS feeds
* [x] RSS normalization
* [x] Duplicate handling
* [x] Full article extraction
* [x] Topic clustering
* [x] Cluster labels and timestamps
* [x] Node.js REST API
* [x] Timeline endpoint
* [x] Ingestion trigger
* [x] Ingestion status

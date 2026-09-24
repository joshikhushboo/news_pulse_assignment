import cors from "cors";
import dotenv from "dotenv";
import express from "express";
import { randomUUID } from "node:crypto";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { MongoClient } from "mongodb";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
dotenv.config({ path: path.join(rootDir, ".env") });
const pythonCommand = process.env.PYTHON_COMMAND || "python";
const mongoUri = process.env.MONGODB_URI;
const databaseName = process.env.MONGODB_DB || "newspulse";
const jobs = new Map();
const app = express();

if (!mongoUri) {
  throw new Error("MONGODB_URI is required in the project root .env file");
}

const mongoClient = new MongoClient(mongoUri, {
  serverSelectionTimeoutMS: 5000,
  connectTimeoutMS: 10000,
});
const database = mongoClient.db(databaseName);
const articles = database.collection("articles");

app.use(cors());
app.use(express.json());

function publicArticle(article) {
  return {
    id: article.id,
    title: article.title || "Untitled article",
    url: article.url || "",
    source: article.source || "Unknown source",
    published: article.published || null,
    summary: article.summary || "",
    cluster: article.cluster ?? null,
    clusterLabel: article.cluster_label || "Related news",
  };
}

function clusterPipeline(source) {
  const match = { cluster: { $ne: null } };
  if (source && source !== "All") match.source = source;
  return [
    { $match: match },
    {
      $group: {
        _id: "$cluster",
        label: { $max: "$cluster_label" },
        articleCount: { $sum: 1 },
        startTime: { $min: "$published" },
        endTime: { $max: "$published" },
      },
    },
    { $sort: { startTime: 1 } },
  ];
}

function clusterResult(row) {
  return {
    id: row._id,
    label: row.label || "Related news",
    articleCount: row.articleCount,
    startTime: row.startTime,
    endTime: row.endTime,
    intensity: row.articleCount,
  };
}

app.get("/clusters", async (_request, response) => {
  try {
    const rows = await articles.aggregate([
      ...clusterPipeline(),
      { $sort: { startTime: -1 } },
    ]).toArray();
    response.json(rows.map(clusterResult));
  } catch (error) {
    console.error(error);
    response.status(500).json({ error: "MongoDB query failed" });
  }
});

app.get("/clusters/:id", async (request, response) => {
  const clusterId = Number(request.params.id);
  if (!Number.isInteger(clusterId)) {
    return response.status(400).json({ error: "Cluster id must be an integer" });
  }

  try {
    const row = (await articles.aggregate([
      { $match: { cluster: clusterId } },
      {
        $group: {
          _id: "$cluster",
          label: { $max: "$cluster_label" },
          articleCount: { $sum: 1 },
          startTime: { $min: "$published" },
          endTime: { $max: "$published" },
        },
      },
    ]).toArray())[0];

    if (!row) return response.status(404).json({ error: "Cluster not found" });

    const clusterArticles = await articles.find({ cluster: clusterId })
      .sort({ published: 1, id: 1 })
      .project({ _id: 0 })
      .toArray();

    response.json({
      ...clusterResult(row),
      articles: clusterArticles.map(publicArticle),
    });
  } catch (error) {
    console.error(error);
    response.status(500).json({ error: "MongoDB query failed" });
  }
});

app.get("/timeline", async (request, response) => {
  try {
    const source = request.query.source || "All";
    const rows = await articles.aggregate(clusterPipeline(source)).toArray();
    const articleFilter = source === "All" ? {} : { source };
    const clusterArticles = await articles.find(articleFilter)
      .sort({ published: 1, id: 1 })
      .project({ _id: 0 })
      .toArray();
    const sources = await articles.distinct("source", { source: { $nin: [null, ""] } });

    response.json({
      sources: sources.sort(),
      clusters: rows.map((row) => ({
        ...clusterResult(row),
        articles: clusterArticles
          .filter((article) => article.cluster === row._id)
          .map(publicArticle),
      })),
    });
  } catch (error) {
    console.error(error);
    response.status(500).json({ error: "MongoDB query failed" });
  }
});

app.get("/articles/latest", async (_request, response) => {
  try {
    const latest = await articles.find({ published: { $nin: [null, ""] } })
      .sort({ published: -1, id: -1 })
      .limit(20)
      .project({ _id: 0 })
      .toArray();
    response.json(latest.map(publicArticle));
  } catch (error) {
    console.error(error);
    response.status(500).json({ error: "MongoDB query failed" });
  }
});

app.get("/api/news", async (_request, response) => {
  try {
    const latest = await articles.find({})
      .sort({ published: -1, id: -1 })
      .project({ _id: 0 })
      .toArray();
    response.json(latest.map(publicArticle));
  } catch (error) {
    console.error(error);
    response.status(500).json({ error: "MongoDB query failed" });
  }
});

app.post("/ingest/trigger", (_request, response) => {
  const jobId = randomUUID();
  const job = { jobId, status: "running", startedAt: new Date().toISOString() };
  jobs.set(jobId, job);
  const scraper = spawn(pythonCommand, ["main.py"], {
    cwd: path.join(rootDir, "scraper"),
    windowsHide: true,
    env: process.env,
  });

  scraper.stdout.on("data", (data) => {
    job.output = `${job.output || ""}${data}`.slice(-4000);
  });
  scraper.stderr.on("data", (data) => {
    job.output = `${job.output || ""}${data}`.slice(-4000);
  });
  scraper.on("error", (error) => {
    job.status = "failed";
    job.error = error.message;
    job.finishedAt = new Date().toISOString();
  });
  scraper.on("close", (code) => {
    job.status = code === 0 ? "completed" : "failed";
    job.exitCode = code;
    job.finishedAt = new Date().toISOString();
  });

  response.status(202).json({ jobId });
});

app.get("/ingest/status/:jobId", (request, response) => {
  const job = jobs.get(request.params.jobId);
  if (!job) return response.status(404).json({ error: "Ingest job not found" });
  response.json(job);
});

const port = Number(process.env.PORT || 3000);

mongoClient.connect()
  .then(async () => {
    await articles.createIndex({ url: 1 }, { unique: true });
    await articles.createIndex({ cluster: 1, published: 1 });
    await articles.createIndex({ published: -1 });
    app.listen(port, () => {
      console.log(`NewsPulse Node API running on port ${port}`);
    });
  })
  .catch((error) => {
    console.error("MongoDB connection failed:", error.message);
    process.exit(1);
  });

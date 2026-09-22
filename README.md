# 🚀 Nexus AI — Delivery Risk Prediction API

A **production-grade, real-time Machine Learning API** that predicts delivery delays for e-commerce orders before they happen. Built on a modern MLOps stack with sub-millisecond feature retrieval, automated model versioning, and full-stack observability — designed to run in production, not just in a notebook.

**🔗 Live Demo:** [nexusai-demo.streamlit.app](https://nexusai-demo.streamlit.app/)

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/MLflow-0194E2?logo=mlflow&logoColor=white" />
  <img src="https://img.shields.io/badge/Feast-Feature_Store-FF6F00" />
  <img src="https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white" />
  <img src="https://img.shields.io/badge/Grafana-F46800?logo=grafana&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Deployed_on-Railway-0B0D0E?logo=railway&logoColor=white" />
  <img src="https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=githubactions&logoColor=white" />
</p>

---

## 📌 Why This Project Exists

Late deliveries are one of the most expensive silent failures in e-commerce — they drive refunds, churn, and negative reviews. **Nexus AI** predicts, at order time, whether a shipment is at risk of arriving late, so operations teams can intervene (re-route, escalate carrier, notify customer) *before* the delay happens instead of reacting after.

This repo isn't a one-off model script — it's built the way a real ML platform team would build it: a served model behind an API, a feature store instead of ad-hoc feature engineering, experiment tracking instead of `model_v_final_final.pkl`, and dashboards that tell you when the model is silently degrading in production.

---

## ✨ Features

- **Real-Time Predictions** — FastAPI backend serving low-latency inference over REST.
- **Feature Store Integration** — **Feast** online store delivers sub-millisecond feature retrieval at prediction time, keeping training/serving features consistent.
- **ML Model Management** — **MLflow** handles experiment tracking, model registry, and versioning, so every deployed model is reproducible and auditable.
- **Production Observability** — **Prometheus** + **Grafana** dashboards track live API latency, throughput, and error rates.
- **Automated CI/CD** — GitHub Actions pipeline runs linting (Ruff), formatting checks, and tests on every push.
- **Cloud Native** — Multi-stage, optimized Docker build deployed on **Railway**.

---

## 🏗️ Architecture

```
                ┌─────────────┐
                │   Client /  │
                │  Streamlit  │
                └──────┬──────┘
                       │ REST
                       ▼
              ┌────────────────┐        ┌────────────┐
              │   FastAPI       │◄──────►│   MLflow   │
              │  serve_api.py   │        │  Registry  │
              └────────┬────────┘        └────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  Feast Online   │
              │  Feature Store  │
              └────────┬────────┘
                       │
                       ▼
              ┌────────────────┐
              │ Prometheus  →   │
              │   Grafana       │
              └────────────────┘
```

1. A prediction request hits the **FastAPI** endpoint.
2. Real-time features are pulled from the **Feast** online store.
3. The latest registered model is loaded via **MLflow** for inference.
4. Request metrics (latency, throughput, errors) are exported to **Prometheus** and visualized in **Grafana**.

---

## 🛠️ Tech Stack

| Category | Technologies |
| :--- | :--- |
| **Language & Framework** | Python 3.12, FastAPI, Uvicorn |
| **Machine Learning** | Scikit-Learn, MLflow |
| **Feature Store** | Feast (Online Store) |
| **Observability** | Prometheus, Grafana, `prometheus-fastapi-instrumentator` |
| **DevOps & CI/CD** | Docker, GitHub Actions, Railway |
| **Package Management** | `uv` (Astral) |

---

## 📂 Project Structure

```text
nexus-ai/
├── .github/workflows/      # CI/CD pipelines (Ruff, Tests)
├── observability/          # Prometheus & Grafana configurations
│   ├── prometheus/
│   └── grafana/
├── pipelines/
│   └── ml/
│       └── serve_api.py    # FastAPI application & endpoints
├── nexus_features/         # Feast feature repository
├── mlflow.db               # Local MLflow tracking database
├── Dockerfile.prod         # Production multi-stage Docker build
├── pyproject.toml          # Project dependencies (managed by uv)
└── README.md
```

---

## ⚡ Getting Started

### Prerequisites
- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) package manager
- Docker (optional, for containerized run)

### 1. Clone & Install
```bash
git clone https://github.com/<your-username>/nexus-ai.git
cd nexus-ai
uv sync
```

### 2. Set Up the Feature Store
```bash
cd nexus_features
feast apply
```

### 3. Start the Observability Stack (Optional)
To run Prometheus and Grafana locally via Docker Compose:
```bash
docker compose -f observability/docker-compose.yml up -d
```
Grafana will be available at `http://localhost:3000` (default login: `admin` / `admin`).

### 4. Run the API
```bash
uv run uvicorn pipelines.ml.serve_api:app --reload --port 8000
```
API docs available at: `http://localhost:8000/docs`

### 5. Run with Docker
```bash
docker build -f Dockerfile.prod -t nexus-ai .
docker run -p 8000:8000 nexus-ai
```

---

## 📡 API Endpoints

Once running, access the interactive Swagger documentation at `http://localhost:8000/docs`.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check (verifies MLflow & Feast status) |
| `GET` | `/metrics` | Prometheus metrics endpoint |
| `GET` | `/docs` | Interactive API documentation (Swagger UI) |
| `POST` | `/predict` | Predict delivery delay risk for an `order_id` |

**Example Request**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
        "order_id": "12345",
        "seller_state": "SP",
        "customer_state": "RJ",
        "product_category": "electronics",
        "freight_value": 25.5
      }'
```

**Example Response**
```json
{
  "order_id": "12345",
  "delay_risk_score": 0.78,
  "risk_level": "HIGH",
  "model_version": "3"
}
```

---

## 📊 Observability Dashboard

The project includes a pre-configured Grafana dashboard to monitor API performance in real-time, backed by Prometheus metrics exposed via `prometheus-fastapi-instrumentator`.

**Key Metrics Tracked:**
- **API Request Rate** — throughput in requests per second
- **Response Latency** — average time taken to process predictions
- **Error Rate** — percentage of 4xx and 5xx HTTP responses

Dashboard config lives in `observability/grafana/` — the same pattern used to catch model or infra degradation before it impacts users.

---

## ☁️ Production Deployment

This application is deployed on **Railway** using a highly optimized, multi-stage, CPU-only Docker build to minimize image size and cold-start times.

- **Live API:** `https://nexus-ai-production.up.railway.app` *(replace with your actual Railway URL)*
- **CI/CD:** Automated deployments trigger on every push to `main` via GitHub Actions.

---

## 🧪 CI/CD

Every push and pull request triggers a GitHub Actions workflow that runs:
- **Ruff** linting and formatting checks
- Automated test suite

This keeps `main` deployable at all times and catches regressions before they reach Railway.

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Format code using Ruff:
   ```bash
   uv run ruff format .
   ```
4. Commit your changes:
   ```bash
   git commit -m "Add amazing feature"
   ```
5. Push to the branch and open a Pull Request.

---

## 🗺️ Roadmap

- [ ] Add SHAP-based explainability endpoint for per-prediction feature attribution
- [ ] Batch prediction endpoint for bulk order scoring
- [ ] Model drift detection with automated retraining trigger
- [ ] Auth layer (API keys / OAuth2) for the public endpoint

---

## 👤 Author

**Umer** — AI/Data Science Engineer in training, building production-style ML systems.

- 🔗 [Live Demo](https://nexusai-demo.streamlit.app/)
- 💼 Open to Junior AI Engineer / Data Science roles

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
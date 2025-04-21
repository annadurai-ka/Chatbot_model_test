# Seller Central AI Chatbot System (Model Deployment)

## Project Overview

The **Seller Central AI Chatbot** is an intelligent assistant designed to help Amazon sellers analyze product reviews and metadata, and answer seller-related queries. It leverages natural language processing and retrieval-based techniques to provide insightful responses for sellers.

Key features:
- **Data-Driven Answers:** Pulls review data from **BigQuery**.
- **Vector Similarity Search:** Uses HuggingFace embeddings + FAISS for relevant review retrieval.
- **Conversational QA Chain:** Powered by **LangChain** with memory for follow-up questions.
- **FastAPI + Cloud Run:** Deployed as a containerized web service.
- **CI/CD:** Fully automated using GitHub Actions.
- **Monitoring:** Cloud Logging + optional BigQuery export.

---

## Deployment Architecture

- **Cloud Run:** Stateless, auto-scaled FastAPI service.
- **BigQuery:** Stores Amazon review datasets.
- **GitHub Actions:** CI/CD pipeline to build + deploy Docker image.
- **Secret Manager:** Holds API keys + service credentials.
- **Cloud Logging + Monitoring:** Tracks chatbot invocations, errors, performance.

---

## Deployment Instructions

### Prerequisites
- GCP project with billing.
- `gcloud` SDK + Docker installed locally.
- Required secrets in Secret Manager (`HF_TOKEN`, `OPENAI_API_KEY`, etc.).
- BigQuery dataset with review data.

### Manual Deployment Steps

#### 1. Build & Push Docker Image
```bash
docker build -t gcr.io/YOUR_PROJECT_ID/sellerchatbot:latest .
docker push gcr.io/YOUR_PROJECT_ID/sellerchatbot:latest
```

#### 2. Deploy to Cloud Run
```bash
gcloud run deploy sellerchatbot-api \
  --image gcr.io/YOUR_PROJECT_ID/sellerchatbot:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account YOUR_SERVICE_ACCOUNT_EMAIL \
  --update-secrets "HF_TOKEN=HF_TOKEN:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest"
```

#### 3. Test the API
```bash
curl -X POST "https://<cloud_run_url>/chat/" \
  -H "Content-Type: application/json" \
  -d '{"asin": "B0TESTASIN", "question": "What do customers say?"}'
```

---

## CI/CD Pipeline (GitHub Actions)

- Triggered on push to `main`.
- Authenticates using `GOOGLE_APPLICATION_CREDENTIALS` secret.
- Builds + tags Docker image with commit SHA.
- Pushes image to Google Container Registry.
- Deploys image to Cloud Run using `gcloud run deploy`.

To set up:
- Add your service account JSON as `GOOGLE_APPLICATION_CREDENTIALS` secret.
- Update `ci.yml` with `PROJECT_ID`, `SERVICE`, and `REGION`.

---

## Monitoring and Logging

- **Cloud Logging:** View logs in GCP console → Logging → Logs Explorer.
- **Log Events:** `chat_started`, `response_generated`, `chatbot_error`.
- **BigQuery (Optional):** Export logs to BigQuery for querying + analysis.
- **Cloud Monitoring:** Request count, error rate, latency metrics available.

Example BigQuery query:
```sql
SELECT DATE(timestamp), COUNT(*)
FROM `project.dataset.chatbot_logs`
WHERE textPayload CONTAINS "chat_started"
GROUP BY 1 ORDER BY 1;
```

---

## Local Development and Testing

### Setup
```bash
git clone https://github.com/aichatbot07/SellerCenteral-ChatBot-System.git
cd SellerCenteral-ChatBot-System
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run Locally
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
uvicorn src.main:app --reload --port 8080
```

### Test Locally
```bash
curl -X POST "http://localhost:8080/chat/" \
  -H "Content-Type: application/json" \
  -d '{"asin": "B0TESTASIN", "question": "Any complaints?"}'
```

---


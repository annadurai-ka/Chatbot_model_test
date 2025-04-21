Thanks! I’ll review your GitHub repo and existing README at https://github.com/aichatbot07/SellerCenteral-ChatBot-System.git, and generate a complete, submission-ready README file. It will include clear markdown formatting, code blocks, setup steps, curl examples, CI/CD details, and monitoring instructions—ready to paste into your repo.

# Seller Central AI Chatbot System (Model Deployment)

## Project Overview

The **Seller Central AI Chatbot** is an intelligent assistant designed to help Amazon sellers analyze product reviews and metadata, and answer seller-related queries. It leverages natural language processing and retrieval-based techniques to provide insightful responses for sellers. Key capabilities of the chatbot include:

- **Data-Driven Answers:** Fetches product **reviews and metadata** from a Google BigQuery database to ground its answers in real customer feedback.
- **Vector Similarity Search:** Converts reviews into embeddings using HuggingFace transformers ([GitHub - aichatbot07/SellerCenteral-ChatBot-System](https://github.com/aichatbot07/SellerCenteral-ChatBot-System#:~:text=,HuggingFace%20Transformers%20for%20embedding%20generation)) and indexes them with **FAISS** for efficient similarity search. This allows the bot to retrieve relevant snippets when a question is asked.
- **Conversational QA Chain:** Uses **LangChain** ([GitHub - aichatbot07/SellerCenteral-ChatBot-System](https://github.com/aichatbot07/SellerCenteral-ChatBot-System#:~:text=,HuggingFace%20Transformers%20for%20embedding%20generation)) to build a conversational Question-Answering chain. The bot combines the retrieved review data with a language model to generate an answer. It can handle follow-up questions by maintaining context (conversation history) in memory.
- **Scalable Deployment:** Containerized as a FastAPI application (served via Uvicorn) for easy deployment on cloud infrastructure. The system is designed to run on Google Cloud Run for scalability and managed hosting.
- **Evaluation and MLOps:** Includes scripts for evaluating retrieval quality (e.g. Precision@k, Recall@k) and answer quality (e.g. BLEU, ROUGE-L) to monitor performance. An offline data pipeline (using Apache Airflow and DVC for data versioning) is provided to ingest and preprocess data into BigQuery, ensuring the chatbot's knowledge base stays up-to-date.

In summary, this project demonstrates an end-to-end solution for an AI-powered chatbot in the Amazon Seller Central context – from data ingestion and model logic to cloud deployment and continuous integration. The following sections detail the cloud architecture, deployment process, CI/CD pipeline, monitoring setup, local development, and the requirements for a video demonstration of the deployed system.

## Deployment Architecture (Cloud Run + GCP + BigQuery + GitHub Actions)

The **deployment architecture** utilizes several Google Cloud Platform (GCP) services alongside our application code and CI/CD tools. The main components are:

- **Google Cloud Run:** The chatbot is deployed as a containerized web service on Cloud Run. Cloud Run provides a fully managed serverless environment to run the Docker container. It auto-scales the service based on incoming requests and abstracts away server management. The FastAPI app runs on port 8080 inside the container, and Cloud Run routes HTTPS requests to the `/chat/` endpoint of the API.
- **Google BigQuery:** BigQuery ([GitHub - aichatbot07/SellerCenteral-ChatBot-System](https://github.com/aichatbot07/SellerCenteral-ChatBot-System#:~:text=,HuggingFace%20Transformers%20for%20embedding%20generation)) serves as the datastore for the chatbot's knowledge base. Product review data and product metadata are stored in BigQuery tables. At runtime, the application uses the BigQuery Python client to fetch relevant reviews (for a given ASIN product ID) which are then processed into the FAISS index for retrieval. BigQuery enables handling large datasets of reviews with fast SQL queries.
- **Secret Manager & Config**: Sensitive credentials and API keys are managed securely. The deployment uses GCP's Secret Manager to store keys (such as HuggingFace tokens, OpenAI API keys, etc.) and a GCP Service Account JSON for BigQuery access. At deployment, these secrets are injected into the Cloud Run service as environment variables. This avoids hard-coding secrets in the code. The application reads configuration (like `HF_TOKEN`, `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, etc.) from environment variables via a config loader.
- **GCP Service Account:** The Cloud Run service runs as a dedicated GCP service account with the necessary IAM roles. This service account is granted access to BigQuery (e.g. **BigQuery Data Viewer** on the dataset) and access to Secret Manager secrets (e.g. **Secret Manager Secret Accessor** role). This allows the running application to query BigQuery and retrieve secrets at runtime using Google-provided credentials, without needing to embed a credentials file. (In this project, the service account used is the default Compute Service Account of the project, which was explicitly specified during deployment.)
- **GitHub Actions (CI/CD):** Automated deployment is set up via a GitHub Actions workflow. On each push to the repository's main branch, the workflow builds the Docker image, pushes it to Google Container Registry, and deploys the new image to Cloud Run. The workflow uses the Google Cloud CLI (`gcloud`) under the hood to handle the build and deployment, as described in the CI/CD section below.
- **Logging and Monitoring:** Cloud Run integrates with **Cloud Logging** by default, so all application logs (including the chatbot’s structured logs and any BigQuery query logs) are captured. We also leverage **Cloud Monitoring** for metrics like request counts, latency, and errors. Optionally, logs can be exported from Cloud Logging to BigQuery for advanced analysis or auditing. This integration allows tracking of chatbot usage and performance over time using SQL queries in BigQuery or dashboards in Cloud Monitoring.

**Data Flow & Interactions:** When a user (or client application) sends a question to the chatbot’s API, the request hits the Cloud Run service (HTTPS endpoint). The FastAPI app parses the request JSON payload (which contains an `asin` and a `question`). The chatbot logic then:

1. Uses the ASIN to query BigQuery for relevant review texts and product info.
2. Embeds the retrieved texts and builds a FAISS index in-memory to find similar content related to the question.
3. Feeds the most relevant snippets into the LangChain QA chain along with the user's question. The chain (with a language model, e.g. via OpenAI or HuggingFace API) generates a contextual answer.
4. Returns the answer as a JSON response to the client.

Throughout this process, important events are logged (e.g., start of chat, no data found, answer generated, etc.), which are viewable in Cloud Logging. The entire architecture is serverless and scalable: BigQuery can handle large data queries, and Cloud Run scales out the container during high load. Development workflows are streamlined by the CI/CD pipeline, and monitoring is in place via logs and metrics.

## Deployment Instructions

This section walks through deploying the Seller Central Chatbot to Google Cloud. It covers setting up the GCP environment, building the Docker container, deploying to Cloud Run (manually and via CI), and testing the live service with `curl`. Before starting, make sure you have the following:

- **GCP Project:** You have access to a Google Cloud project with billing enabled.
- **Google Cloud SDK:** `gcloud` CLI is installed and authenticated (`gcloud auth login`) on your local machine.
- **Project Setup:** Ensure the necessary GCP services are enabled: Cloud Run, BigQuery, Artifact Registry (for storing container images, or Container Registry), and Secret Manager (for managing secrets). Also create or identify a BigQuery dataset/table that contains the product reviews data required by the chatbot.
- **Service Account:** Create a GCP Service Account (or use the default Compute service account) that the Cloud Run service will run as. Grant it permissions to BigQuery (e.g. **BigQuery Data Viewer** on the dataset or project) and Secret Manager **Secret Accessor** for the specific secrets you'll use.
- **Application Secrets:** Obtain all required API keys and credentials:
  - HuggingFace API token (`HF_TOKEN`) – for embedding model access.
  - DeepSeek API key (`DEEPSEEK_API_KEY`) – if used for any external service.
  - OpenAI API key (`OPENAI_API_KEY`) – if using OpenAI for answer generation.
  - (Any other keys like `GROQ_API_KEY`, LangFuse keys if applicable.)
  - Service account JSON for BigQuery access (only needed if not relying on GCP service account identity).
  
  Store these secrets securely. **If using Secret Manager (recommended):** create a secret for each (e.g., a secret named `HF_TOKEN` containing your HuggingFace token, and so on for each key, as well as a secret named `GOOGLE_APPLICATION_CREDENTIALS` containing the content of your service account JSON if you plan to use the JSON file). You can create secrets via the Cloud Console or using gcloud (for example: `echo -n "YOUR_HF_TOKEN_VALUE" | gcloud secrets create HF_TOKEN --data-file=-`).

With the setup done, follow these steps to deploy:

**1. Build the Docker Container Image**  
The repository includes a `Dockerfile` that defines the container environment. It is based on **Python 3.9 slim**, installs the Python dependencies from `requirements.txt`, and sets the entrypoint to Uvicorn serving the FastAPI app on port 8080 (see the `CMD ["uvicorn", "src.main:app", ...]` in the Dockerfile). You can build the image locally and push to Google Container Registry (GCR) or Artifact Registry:

- *Option A: Use Google Cloud Build (gcloud)* – This is the simplest method if you have the gcloud CLI:
  ```bash
  # from the root of the repository:
  gcloud config set project YOUR_GCP_PROJECT_ID
  gcloud builds submit --tag gcr.io/YOUR_GCP_PROJECT_ID/sellerchatbot:latest .
  ```
  This command will upload your code to Google Cloud and build it on GCP's infrastructure, then store the image in the GCR registry (`sellerchatbot` is an example image name; you can choose another name).

- *Option B: Build and push with Docker manually* – Ensure Docker is running locally, then:
  ```bash
  docker build -t gcr.io/YOUR_GCP_PROJECT_ID/sellerchatbot:latest .
  docker push gcr.io/YOUR_GCP_PROJECT_ID/sellerchatbot:latest
  ```
  This will build the image locally and push it to your GCP project's container registry. (You might need to run `gcloud auth configure-docker` once to allow Docker to push to gcr.io.)

**2. Deploy to Cloud Run (Manual via gcloud)**  
Once the container image is available in the registry, deploy it to Cloud Run:
```bash
gcloud run deploy sellerchatbot-api \
  --image gcr.io/YOUR_GCP_PROJECT_ID/sellerchatbot:latest \
  --platform managed --region us-central1 \
  --allow-unauthenticated \
  --service-account YOUR_SERVICE_ACCOUNT_EMAIL \
  --memory 4Gi --timeout 300s \
  --update-secrets "HF_TOKEN=HF_TOKEN:latest,DEEPSEEK_API_KEY=DEEPSEEK_API_KEY:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,GOOGLE_APPLICATION_CREDENTIALS=GOOGLE_APPLICATION_CREDENTIALS:latest"
```
In the above command:
  - `sellerchatbot-api` is the name of the Cloud Run service (you can name it differently).
  - `--platform managed --region us-central1` deploys to the specified region on the fully managed Cloud Run.
  - `--allow-unauthenticated` makes the service publicly accessible (no auth token needed to invoke).
  - `--service-account` sets the service to run as the service account we configured (replace `YOUR_SERVICE_ACCOUNT_EMAIL` with the email of the SA). This account's permissions will be used to access BigQuery and secrets.
  - `--update-secrets` attaches the secrets from Secret Manager as environment variables in the container. For example, `HF_TOKEN=HF_TOKEN:latest` means it will fetch the latest version of the Secret Manager secret named "HF_TOKEN" and set an env var `HF_TOKEN` with that value inside the container. Similarly for the other secrets including `GOOGLE_APPLICATION_CREDENTIALS` (which would provide the JSON credentials if needed). If you are using the service account identity for BigQuery, the `GOOGLE_APPLICATION_CREDENTIALS` secret may not be strictly required – Google’s ADC (Application Default Credentials) will use the service account's identity automatically. However, if your code explicitly expects a JSON key, providing it via secret ensures compatibility.

   *Note:* The memory (4Gi) and timeout (300s) settings can be adjusted based on the needs of the model (e.g., if embedding or QA chain is heavy). Ensure your Cloud Run service account has access to the specified secrets (Secret Manager will enforce IAM).

After running the deploy, Cloud Run will output the service URL (something like `https://sellerchatbot-api-<randomhash>-uc.a.run.app`). You can also retrieve the URL with:
```bash
gcloud run services describe sellerchatbot-api --region us-central1 --format "value(status.url)"
```

**3. Set Up GitHub Actions for CI/CD (Optional)**  
Instead of manual builds and deploys, you can rely on the included GitHub Actions workflow to automate this process on every code push. The repo’s workflow file is located at [`.github/workflows/ci.yml`](.github/workflows/ci.yml), and it already contains the steps to authenticate to Google Cloud, build the Docker image, push it, and deploy to Cloud Run (mirroring the manual steps above). To use this:

   - Go to your GitHub repository Settings -> Secrets (or Settings -> Actions -> Secrets and variables -> Repository secrets) and add a secret named `GOOGLE_APPLICATION_CREDENTIALS`. The value should be the **JSON content** of the Google Cloud service account key (that has permissions to deploy to Cloud Run). This is used by the workflow to authenticate (`google-github-actions/auth@v1`).
   - Open the `ci.yml` file and update the environment variables under `env:` if needed:
     - `PROJECT_ID` should be your GCP project ID.
     - `SERVICE` should be your desired Cloud Run service name (e.g., "sellerchatbot-api").
     - `REGION` should match where you want to deploy (e.g., "us-central1").
   - Ensure the Secret Manager on GCP has all the runtime secrets as discussed. The workflow uses `gcloud run deploy --set-secrets` just like the manual step, so it expects those secrets to exist in GCP. (If you prefer not to use Secret Manager, you'd have to modify the deploy command to use `--update-env-vars` with values stored in GitHub Secrets — not covered here for brevity and security considerations.)
   - Commit and push your changes. The GitHub Actions pipeline will trigger on push to the **main** branch by default (as specified by `on: push` to main in the workflow). You can monitor the progress in the Actions tab of your GitHub repo. If configured correctly, you should see steps for checkout, Google Cloud auth, Docker build/push, and Cloud Run deploy. A successful run means your new code is live on Cloud Run.

Using the CI/CD pipeline ensures that any update to your code repository will automatically roll out to the Cloud Run service, providing a robust continuous deployment mechanism.

**4. Test the Deployed Service (API)**  
After deployment, you should verify that the chatbot API is working. You can use `curl` from the command line to send a test request to the `/chat/` endpoint. The endpoint expects a POST request with a JSON body containing an `asin` (Amazon product ID) and a `question`. For example:

```bash
# Replace <CLOUD_RUN_URL> with your service URL from the deploy step
curl -X POST "<CLOUD_RUN_URL>/chat/" \
  -H "Content-Type: application/json" \
  -d '{
        "asin": "B0EXAMPLEASIN", 
        "question": "What do customers say about the battery life?"
      }'
```

If everything is set up correctly, the service will fetch the reviews for the product `B0EXAMPLEASIN` from BigQuery, run the QA chain, and return a JSON response with an answer. A typical successful response looks like:

```json
{
  "asin": "B0EXAMPLEASIN",
  "question": "What do customers say about the battery life?",
  "answer": "Many customers mention that the battery life lasts around 10 hours on a single charge, which they find satisfactory for daily use."
}
```

(The exact answer will depend on the content of your BigQuery reviews for that ASIN and the behavior of the language model. If the ASIN is not found in the database, you should get an appropriate message like "No review data found for the provided ASIN." as defined in the code.)

> **Tip:** You can also test the service from the GCP Console. In Cloud Run, click on your service and use the "Testing" tab to send a JSON request. Alternatively, tools like Postman or HTTPie can be used for testing the REST endpoint.

## CI/CD Pipeline with GitHub Actions

The project implements a Continuous Integration/Continuous Deployment pipeline using **GitHub Actions**. The workflow file [`ci.yml`](.github/workflows/ci.yml) encapsulates the build and deploy steps required to keep the Cloud Run service up to date. Here is an overview of the CI/CD pipeline:

- **Trigger:** The workflow is configured to run on every push to the `main` branch (and can be extended to pull requests or other triggers as needed). This means that as soon as you push new code or merge a pull request into main, the deployment process will kick off automatically ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=on%3A)).
- **Checkout and Setup:** The first steps have the runner check out the repository code ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=steps%3A)). Then, it authenticates to Google Cloud using the service account credentials stored in the `GOOGLE_APPLICATION_CREDENTIALS` secret ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=,key%20stored%20in%20GitHub%20Secrets)). It also sets up the gcloud SDK on the runner with the target project and installs the necessary components (like `gcloud` and Docker support) ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=,Cloud%20SDK)).
- **Docker Build and Push:** The workflow uses Docker to build the image from the repository. It tags the image as `gcr.io/PROJECT_ID/SERVICE_NAME:$GITHUB_SHA` (using the commit SHA as the image tag for traceability) ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=)). After a successful build, it pushes the image to Google Container Registry ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=)). Using the commit SHA ensures each deployment is uniquely identifiable and allows easy rollback to specific versions if needed.
- **Deploy to Cloud Run:** Once the image is pushed, the workflow deploys it to Cloud Run in the specified region ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=,Run)). The deploy command is equivalent to what was shown in the manual instructions:
  - It specifies the service name and image URL with tag ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=run%3A%20)).
  - It passes the same flags for platform, region, and unauthenticated access ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=gcloud%20run%20deploy%20%24,)).
  - It allocates adequate memory and timeout for the container ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=)).
  - It sets the service account to run as (the one we configured with proper IAM roles) ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=)).
  - It injects all the required secrets from Secret Manager into the service's environment ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=)) ([SellerCenteral-ChatBot-System/.github/workflows/ci.yml at main · aichatbot07/SellerCenteral-ChatBot-System · GitHub](https://github.com/aichatbot07/SellerCenteral-ChatBot-System/blob/main/.github/workflows/ci.yml#:~:text=)). This includes API keys and the credentials JSON if needed. (The secrets must already exist in Secret Manager; the workflow does not create them but just references them.)
- **Result:** Cloud Run rolls out the new revision of the service with the updated image. The workflow will complete with a success status if everything went smoothly. In the Cloud Run console, you will see a new revision corresponding to the deployment. The GitHub Actions run log will show each step's output or any errors if they occurred.

By using this CI/CD pipeline, developers do not have to manually build or deploy the application each time. It reduces human error and ensures that the **source of truth** (the Git repository) is directly tied to the deployed application state. For example, when you update the chatbot's logic or fix a bug, you simply push the changes to GitHub; the pipeline will test (if tests were added, you could extend the workflow to run `pytest` before building), build the container, and update the Cloud Run service.

**Setting up the CI/CD** (if you fork or replicate this repository):
- Remember to add the `GOOGLE_APPLICATION_CREDENTIALS` secret in your GitHub repo (with your service account JSON).
- Adjust `PROJECT_ID`, `SERVICE`, and `REGION` in the workflow file to match your environment.
- Make sure the service account used has the IAM roles: **Cloud Run Admin**, **Cloud Build Service Account** (if using Cloud Build), **Storage Admin** (to push to GCR), and possibly **Secret Manager Admin/Accessor** for reading secrets. An easy approach is to grant the service account the pre-defined **Cloud Run Developer** role and additionally **Secret Manager Secret Accessor** on the specific secrets.
- (Optional) Add any additional steps you need, such as running tests or notifications on failure, to the workflow.

Once configured, try making a small commit to trigger the workflow and watch the Actions console for the deployment logs. Upon success, your Cloud Run service will have the latest code. This continuous deployment approach is essential for agile iteration and is a key part of the **MLOps** and DevOps best practices demonstrated by this project.

## Monitoring and Logging via Cloud Logging + BigQuery

Monitoring the deployed chatbot is crucial to ensure it is performing well and to troubleshoot issues. This project takes advantage of GCP’s logging and monitoring services:

- **Cloud Logging (Stackdriver):** All logs from the application running on Cloud Run are automatically sent to Google Cloud Logging. This includes HTTP request logs (with details like HTTP status, latency, etc.) as well as any application logs we produce. In our code, we've set up logging to output JSON-formatted logs for key events (using Python's logging and `logger.info/json.dumps` in the chatbot code). For example, when a chat request starts, we log an event `"chat_started"` with the ASIN and question, and when an answer is generated, we log `"response_generated"` with the content of the answer. These logs can be viewed in the Cloud Console under Logging > Logs Explorer. You can filter by resource type "Cloud Run Revision" and your service name to see only logs from your chatbot service. Each log entry will show the payload we logged as well as metadata (like timestamp, severity, trace ID for request correlation, etc.).

- **Cloud Monitoring:** Cloud Run automatically records metrics such as the number of requests, request latency, CPU/memory utilization, etc. You can view basic metrics by clicking on your service in the Cloud Run console – it shows request count, error rate, and latency distributions. For more advanced monitoring, you can use Cloud Monitoring (Stackdriver) to create custom dashboards or alerts. For instance, you could set up an alert if the error rate (HTTP 5xx responses) exceeds a certain threshold, which could indicate the model or BigQuery queries are failing.

- **BigQuery for Analytics:** While Cloud Logging is great for real-time log inspection, **BigQuery** can be used to perform deeper analysis on logs or application data over time. There are a couple of ways BigQuery comes into play:
  - *BigQuery as the data source:* (This is the primary use in our chatbot logic.) The content the model uses to answer questions comes from BigQuery. Monitoring data freshness or the volume of data in BigQuery can be done with BigQuery's own console or by queries. For example, you might periodically run a BigQuery COUNT query on the reviews table to ensure new data is being added (if an ongoing pipeline feeds it).
  - *Exporting logs to BigQuery:* We can create a logs sink that continuously exports Cloud Run logs to a BigQuery table. This is optional, but very powerful. By doing this, all those JSON log events (questions asked, answers given, etc.) can accumulate in BigQuery. You can then write SQL queries to analyze them: e.g., to find the most common questions, to track the frequency of certain errors, or to analyze average answer length over time. To set this up, you'd go to Logging > Logs Router, create a sink with a filter for your Cloud Run logs, and choose BigQuery as the destination. Once logs are in BigQuery, the data science team could even use it for further analysis or to feed back into model improvement (e.g., identifying unanswered questions or potential new training data).
  - *Storing model evaluation results:* The project includes an offline evaluation module (under `model_evaluation/`). As you evaluate the model responses (for example, computing BLEU scores comparing the bot's answer to a reference), you might store those results in BigQuery as well, to track performance across model versions. This isn't implemented by default, but the infrastructure is in place: you could have a BigQuery table for evaluation metrics and insert a new row each time you run an evaluation script on a new model or new data. Over time, this becomes a valuable record of model performance.

- **Error Tracking:** The FastAPI app will return HTTP 500 errors for exceptions. These will show up in Cloud Run logs and increase the error count metric. Our code logs the exception detail (`chatbot_error` events with stack trace) which helps debugging. Cloud Logging can be configured to trigger alerts on certain log patterns (for example, any `ERROR` level log or the presence of `"chatbot_error"` event can send an email alert).

- **Inspecting BigQuery usage:** Since the chatbot executes queries on BigQuery for each request (to fetch reviews by ASIN), you can monitor BigQuery for query count or bytes scanned. In the BigQuery console, under Admin > Query history or Metrics, you can see how each query performed. Each query by the chatbot will use the service account's identity, so you can identify them. For cost monitoring, ensure the queries are optimized (e.g., the BigQuery SQL in `Data/fetch_reviews.py` should select only needed columns and use appropriate filtering by ASIN, which is likely indexed by partitioning or clustering on that field if the table is large).

Overall, the combination of Cloud Run’s logging and monitoring and BigQuery’s analytic capabilities gives a comprehensive view of the system in production. In practice, after deployment you should:

- Use **Logs Explorer** to tail the logs as you send test queries (this will show you the timeline of events for each query, e.g., you'll see a `chat_started` log followed by `retriever_ready` and `response_generated`).
- Check Cloud Run’s metrics after some usage to see if the scaling behavior and latency are within expectations.
- If needed, set up a BigQuery logs sink to analyze usage patterns over a longer period or to create an interactive dashboard of questions asked and answered by the bot.

By regularly monitoring these logs and metrics, you can ensure the chatbot remains reliable and you can quickly react to any issues (like if BigQuery credentials expired, or an API key is invalid, you'd see errors in logs). It also provides insight into how users are interacting with the chatbot, which is valuable for future improvements.

## Local Development and Testing

For development and testing purposes, you may want to run the chatbot system locally. This allows you to debug issues and run the pipeline without deploying to the cloud each time. Below are instructions for setting up a local dev environment and running tests:

**1. Setting up the environment:**  
Clone the repository to your local machine:
```bash
git clone https://github.com/aichatbot07/SellerCenteral-ChatBot-System.git
cd SellerCenteral-ChatBot-System
```
Ensure you have **Python 3.9+** installed. It's recommended to use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # (On Windows: venv\Scripts\activate)
```
Install the required Python packages:
```bash
pip install -r requirements.txt
```
This will install FastAPI, Uvicorn, google-cloud-bigquery, langchain, faiss-cpu, and other dependencies.

**2. Configuration:**  
For local testing, you'll need access to BigQuery and the various API keys just like in production. The simplest approach is to set environment variables on your machine for all the keys (HF_TOKEN, OPENAI_API_KEY, etc.). You can do this by creating a `.env` file or exporting variables in your shell. Also, you need to authenticate to Google Cloud for BigQuery access:
- Obtain your Google Cloud service account JSON key (the same one used in deployment, or any account with BigQuery read access).
- Set the environment variable to point to it:
  ```bash
  export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account.json"
  ```
  This will allow the BigQuery client to find the credentials. Alternatively, use `gcloud auth application-default login` to use your own account for BigQuery access in dev (not recommended for production, but fine for a quick test).

**3. Running the API server locally:**  
You can start the FastAPI server (Uvicorn) locally to test the chatbot:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```
The `--reload` flag makes the server auto-restart on code changes (useful during development). Once it’s running, open a browser or use curl to test:
```
curl -X POST "http://localhost:8080/chat/" \
  -H "Content-Type: application/json" \
  -d '{"asin": "B0TESTASIN", "question": "Sample question?"}'
```
If you have the BigQuery access configured properly and the ASIN exists in your data, you should get a JSON response from the local server. You can add print statements or use a debugger to step through the code in `src/chatbot_model.py` or other modules to inspect behavior.

**4. Running the Data Pipeline (optional):**  
The repository contains a `Data_pipeline/` directory with scripts (and Airflow DAGs) that presumably take raw data (like JSONL files of reviews) and load them into BigQuery, perform preprocessing, bias detection, etc. If you want to regenerate or update the BigQuery data, you can run these scripts. For example:
```bash
python Data_pipeline/dags/fetch_data.py       # Fetch raw data (perhaps from an API or file)
python Data_pipeline/dags/data_process.py     # Process/clean the raw data
python Data_pipeline/dags/bias_detection.py   # (Optional) detect biases in data
python Data_pipeline/dags/dataflow_processing.py  # Additional processing, maybe using Dataflow
python Data_pipeline/dags/sellerId_check.py   # Validate or augment data with seller IDs
python Data_pipeline/dags/mlops_airflow.py    # Integrate with Airflow (if using Airflow scheduler)
```
These are just the names of scripts; refer to the code/comments in those files for details on usage. If you have **Apache Airflow** installed, you can instead use the Airflow UI to run the pipeline as a DAG (there is an Airflow YAML in `.github/workflows/airflow_pipeline.yml` which might relate to running Airflow in CI). For local simplicity, direct Python execution or using DVC is sufficient:
   - The project supports **DVC (Data Version Control)** for data tracking. If DVC is set up, you might pull sample data using `dvc pull` (if a remote is configured; check for `.dvc` files).
   - Ensure any paths or project IDs inside these scripts match your setup (for example, the BigQuery dataset name).

**5. Running Tests:**  
Under the `tests/` directory, there may be unit tests for certain components (for instance, `tests/test_pipeline.py`). You can run the test suite with:
```bash
pytest tests/
```
Make sure you have any necessary test fixtures or environment variables set so that tests can run (the test code may be expecting a certain environment or sample data). The tests will help verify that individual pieces like the data pipeline or retrieval functions are working as expected.

**6. Iterating locally:**  
You can freely modify the code (for example, tweak the prompt for the LangChain QA chain, or try a different embedding model) and test it locally. Once satisfied, you can push changes to GitHub to trigger the CI/CD and deploy them.

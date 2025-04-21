# SellerCentral-ChatBot-System

## Project Overview

SellerCentral-ChatBot-System is a cloud-based conversational chatbot designed to assist e-commerce sellers with common queries and tasks. It provides an interactive question-answering service through a web API endpoint, allowing sellers to get instant support. The chatbot is deployed on **Google Cloud Platform (GCP)** using **Cloud Run**, which means it runs as a serverless containerized application. This design allows the chatbot to scale automatically based on demand without requiring manual server management ([Cloud Run | xMatters](https://www.xmatters.com/integration/google-cloud-run#:~:text=Google%20Cloud%20Run%20is%20a,almost%20instantaneously%20depending%20on%20traffic)). The project emphasizes *model deployment and monitoring* rather than model training – in fact, no model training or retraining is performed as part of this system. Instead, a pre-built or pre-trained model is integrated into the application and served to users. 

Key features of the SellerCentral-ChatBot-System include:

- **Stateless Chatbot API**: The chatbot logic (e.g., a machine learning model or rule-based system) is encapsulated in a container that responds to HTTP requests. This makes it easy to query the chatbot from any client (web, mobile, etc.) via simple HTTP calls.
- **Cloud Deployment**: By leveraging GCP Cloud Run, the chatbot benefits from high availability and automatic scaling. Cloud Run manages the underlying infrastructure, scaling the container instances up or down (even to zero) based on incoming traffic, which optimizes cost and performance ([Cloud Run | xMatters](https://www.xmatters.com/integration/google-cloud-run#:~:text=Google%20Cloud%20Run%20is%20a,almost%20instantaneously%20depending%20on%20traffic)).
- **Continuous Deployment**: The project uses a CI/CD pipeline with GitHub Actions to automatically build and deploy new versions of the chatbot. Every code update can be seamlessly rolled out to Cloud Run, ensuring that the live service is always up-to-date.
- **Monitoring & Logging**: The system implements basic model monitoring through logging. Each time the chatbot is started or handles a conversation, and whenever an error occurs, the event is logged. These logs are exported to **BigQuery** for analysis. By querying the logs, one can track metrics such as *how often the chatbot is invoked* and *how many errors occur over time*. This provides insights into usage patterns and system reliability.

In summary, SellerCentral-ChatBot-System is a **serverless chatbot application** with an emphasis on reliable deployment and monitoring. It is suitable for scenarios where an AI chatbot assists users (in this case, sellers) without the overhead of managing infrastructure or continuously retraining models.

## Deployment Architecture

The deployment architecture of the SellerCentral-ChatBot-System comprises several GCP services and integration points, as shown below:

- **Google Cloud Run (Service)** – Cloud Run hosts the chatbot application in a Docker container. It is a fully managed, serverless platform for running stateless containers triggered by web requests ([Cloud Run | xMatters](https://www.xmatters.com/integration/google-cloud-run#:~:text=Google%20Cloud%20Run%20is%20a,almost%20instantaneously%20depending%20on%20traffic)). The chatbot container is deployed to Cloud Run, allowing it to automatically scale with incoming traffic and scale down when idle. Cloud Run abstracts away server management, so we don't worry about VMs or Kubernetes clusters. The service is typically configured to allow public (unauthenticated) access, so that users can directly send requests to the chatbot’s HTTP endpoint. There is no separate model training component in the architecture; the model is loaded and served within this runtime container.

- **GitHub Actions (CI/CD Pipeline)** – The code repository (for example, on GitHub) is linked to an automated pipeline using GitHub Actions. Whenever new code is pushed to the repository (e.g., merged into the main branch), the CI/CD workflow triggers. The pipeline builds the Docker image for the chatbot, runs tests (if any), pushes the image to a container registry, and then deploys the new image to Cloud Run ([From Code to Cloud: GitHub Actions for Cloud Run Deployment | by Azeez | Medium](https://azeezz.medium.com/from-code-to-cloud-github-actions-for-cloud-run-deployment-dc1304573642#:~:text=Github%20Actions%20is%20a%20continuous,with%20a%20Service%20Account%20Key)) ([From Code to Cloud: GitHub Actions for Cloud Run Deployment | by Azeez | Medium](https://azeezz.medium.com/from-code-to-cloud-github-actions-for-cloud-run-deployment-dc1304573642#:~:text=machine%20,on%20the%20cloud%20run%20service)). This ensures continuous integration and deployment: any update to the chatbot’s code can be quickly rolled out to production without manual intervention. The GitHub Actions workflow uses Google Cloud’s official or community-provided actions to authenticate with GCP and execute the deployment commands.

- **Container Registry/Artifact Registry** – As part of deployment, the Docker image for the chatbot is stored in a registry. This could be Google Container Registry (GCR) or Artifact Registry. The CI pipeline builds the image and tags it (for example, with the Git commit or version), then pushes it to the registry. Cloud Run then pulls this image from the registry during deployment. The registry is Google-managed and requires proper authentication (handled by the CI workflow using GCP credentials).

- **Cloud Logging and BigQuery (Monitoring)** – Cloud Run services automatically send logs to Google Cloud Logging by default ([Logging and viewing logs in Cloud Run  |  Cloud Run Documentation  |  Google Cloud](https://cloud.google.com/run/docs/logging#:~:text=Cloud%20Run%20has%20two%20types,automatically%20sent%20to%20Cloud%20Logging)). In this architecture, a Cloud Logging **sink** is configured to export relevant logs to **BigQuery** in near real-time. Two custom metrics are tracked via log entries:
  - *Chatbot Started Count*: incremented/logged each time the chatbot application starts handling a new session or request (this could be for each new chat session or each invocation, depending on how it's instrumented).
  - *Chatbot Error Count*: incremented/logged whenever an error or exception occurs in the chatbot (for example, failure to process a message).
  
  The log sink filters the Cloud Run logs to capture these events and stores them in a BigQuery table for analysis. By exporting logs to BigQuery, we can run SQL queries to count occurrences of these events over time ([View logs routed to BigQuery  |  Cloud Logging  |  Google Cloud](https://cloud.google.com/logging/docs/export/bigquery#:~:text=This%20document%20explains%20how%20you,also%20describes%20the%20%20213)). This serves as a lightweight monitoring solution for usage (how many chats were started) and reliability (how many errors happened). Optionally, these logs could also be used to set up alerts or dashboards (for instance, using Data Studio or Cloud Monitoring by linking BigQuery data), but the core idea is that the metrics are **logged** and **queried** rather than using a complex monitoring system. All other application logs (like debug info or general audit logs) also reside in Cloud Logging and can be viewed via the Logs Explorer in GCP, but only the key metrics are routed to BigQuery for custom analysis.

**Note:** The architecture does not include a training or data pipeline because *no model training/retraining is involved*. The focus is on deploying the inference service (the chatbot) and monitoring its runtime behavior. All components (Cloud Run, Logging, BigQuery, etc.) are in the cloud, making the system highly available and maintainable with minimal on-premise requirements.

## Deployment Instructions

Deploying the SellerCentral-ChatBot-System involves setting up the cloud environment, configuring credentials, and either relying on the CI/CD pipeline or manually deploying. Below are step-by-step instructions for a successful deployment:

1. **Prerequisites and Environment Setup**:  
   - **Google Cloud Project**: Ensure you have access to a GCP project with billing enabled. Note the **Project ID** as it will be needed for deployment configuration. If you don't have a project, create one via the GCP Console. Also, enable the **Cloud Run API** and **BigQuery API** for this project (you can do this through the console or with `gcloud services enable run.googleapis.com bigquery.googleapis.com`).  
   - **Google Cloud SDK (gcloud CLI)**: Install the Google Cloud SDK to get the `gcloud` command-line tool ([Google Cloud CLI documentation](https://cloud.google.com/sdk/docs#:~:text=Google%20Cloud%20CLI%20documentation%20Quickstart%3A,CLI%20%C2%B7%20Managing%20gcloud)). This tool will be used for local testing or manual deployment. You can install it from Google’s documentation (for example, on Ubuntu or Mac, download the installer or use a package manager). After installation, run `gcloud init` and `gcloud auth login` to authenticate and set the default project.  
   - **Docker**: Install Docker on your local system if you plan to build or run the container image locally. Docker is required to build the container image that Cloud Run will execute. Verify that running `docker --version` works.  
   - **Source Code**: Clone the repository for SellerCentral-ChatBot-System to your local machine:  
     ```bash
     git clone https://github.com/your-username/SellerCentral-ChatBot-System.git
     cd SellerCentral-ChatBot-System
     ```  
     (Use the actual repository URL or path as appropriate). The repository should contain the application code, a Dockerfile, and configuration files including the GitHub Actions workflow.  
   - **Configuration**: Review any configuration files or environment variable templates (for example, a `.env.example` file) in the repository. Prepare a `.env` file or set environment variables as needed (for instance, API keys or other secrets the chatbot might require to function). Common variables might include `PORT` (Cloud Run sets this automatically, usually 8080), or any model-specific settings. These should be documented in the repo. 

2. **Authentication and Permissions Setup**:  
   Deploying to Cloud Run via GitHub Actions requires granting the pipeline access to your GCP project:
   - **Service Account**: Create a GCP Service Account that will be used by GitHub Actions. For example, in the GCP Console or using the gcloud CLI, create a service account (e.g., name it `github-deployer`). Grant this service account the necessary IAM roles:
     - *Cloud Run Admin* – allows deploying new revisions to Cloud Run.
     - *Cloud Run Service Agent* – (if not included in admin) allows managing Cloud Run services.
     - *Artifact Registry Writer* (or *Storage Object Admin* if using Container Registry) – allows pushing Docker images to your project's registry.
     - *BigQuery Data Editor* (optional, only if your deployment process or monitoring needs to create tables or write to BigQuery; reading logs doesn't require this, as logging will handle BigQuery writes).
     - *Service Account User* – if the GitHub Actions workflow will impersonate this service account, it might need this role on itself.
   - **Generate Key**: For the service account, create a JSON key (in the IAM & Admin > Service Accounts section, select your service account, and add a key). This will download a JSON credentials file. **Keep it secure** and do not commit it to your repo.
   - **GitHub Secrets**: In your GitHub repository settings, add the necessary secrets so the Actions workflow can authenticate:
     - `GCP_PROJECT_ID`: your Google Cloud project ID.
     - `GCP_SA_KEY`: the content of the service account JSON key (you can copy-paste the JSON or encode it as base64 as required by your workflow).
     - (Alternatively, you might use OpenID Connect Workload Identity Federation instead of a JSON key. In that case you'd configure `google-github-actions/auth@v2` with a workload identity provider. But using the JSON key is simpler to start with.)
   - **Permissions Confirmation**: Locally, you can also authenticate with GCP to test permissions. Run: `gcloud auth activate-service-account --key-file path/to/key.json --project YOUR_PROJECT_ID` to impersonate the service account, then try a dry-run deployment command (see next step) to ensure permissions are correct.

3. **Deployment via GitHub Actions**:  
   The repository includes a GitHub Actions workflow (YAML file in `.github/workflows/`) that automates the build and deployment. You generally **do not need to run deployment scripts manually** – the CI/CD pipeline will do it on triggers. However, you should know how it works and how to trigger it:
   - **Continuous Deployment Trigger**: Usually, the workflow is configured to run on certain events. Commonly, pushing a commit to the `main` branch or pushing a tagged release will start the pipeline. Check the YAML file (look for the `on:` section) to see if it's triggered on `push`, `pull_request`, or manual `workflow_dispatch`. To initiate a deployment, you can push a new commit (for example, after making a small change or bumping a version). If the pipeline is set up for manual triggers, go to the Actions tab in GitHub, select the workflow, and manually trigger a run.
   - **Build and Deploy Steps**: The GitHub Actions workflow will perform roughly the following steps:
     1. **Checkout Code** – pulls the latest code from the repository.
     2. **Authenticate to GCP** – uses the provided service account credentials to authenticate (`google-github-actions/auth` action or `gcloud auth activate-service-account` in a step). This grants the workflow permission to use gcloud and push images.
     3. **Build Container Image** – calls Docker to build the image from the Dockerfile. For example, it might run `docker build -t gcr.io/$PROJECT_ID/sellercentral-chatbot:$GITHUB_SHA .` to tag the image with the commit SHA. If using Google Artifact Registry, the image name will use your region’s repository URL (e.g., `REGION-docker.pkg.dev/PROJECT_ID/REPO_NAME/image:tag`).
     4. **Push Image to Registry** – after a successful build, the workflow pushes the image to the registry using Docker push. The credentials set up earlier allow this push to succeed.
     5. **Deploy to Cloud Run** – finally, the workflow deploys the new image to Cloud Run. This is done with a command such as `gcloud run deploy sellercentral-chatbot-service --image gcr.io/PROJECT_ID/image:tag --region REGION --platform managed --allow-unauthenticated` (the exact command flags might vary). The service name on Cloud Run is specified (e.g., `sellercentral-chatbot-service`), along with the image and region. The `--allow-unauthenticated` flag ensures the service is publicly reachable (no auth required). Other parameters like memory/CPU allocation, scaling limits, or environment variables might also be set in this command or via a Cloud Run service YAML definition if used.  
     
     The GitHub Actions log will show each step and whether it succeeded. If all goes well, the Cloud Run deployment step will output the URL of the service (or you can retrieve it from the Cloud Run console). The pipeline effectively containerizes the application and updates the live service in an automated fashion, aligning with best practices for CI/CD in cloud deployments ([From Code to Cloud: GitHub Actions for Cloud Run Deployment | by Azeez | Medium](https://azeezz.medium.com/from-code-to-cloud-github-actions-for-cloud-run-deployment-dc1304573642#:~:text=Github%20Actions%20is%20a%20continuous,with%20a%20Service%20Account%20Key)) ([From Code to Cloud: GitHub Actions for Cloud Run Deployment | by Azeez | Medium](https://azeezz.medium.com/from-code-to-cloud-github-actions-for-cloud-run-deployment-dc1304573642#:~:text=machine%20,on%20the%20cloud%20run%20service)).
   - **Manual Deployment Option**: In some cases, you might want to deploy manually (for example, for initial setup or debugging). If you have the gcloud CLI set up locally and Docker image built, you can deploy with one command using gcloud:
     ```bash
     # Build the image (if not already built by CI)
     docker build -t gcr.io/<YOUR_PROJECT_ID>/sellercentral-chatbot:latest .
     docker push gcr.io/<YOUR_PROJECT_ID>/sellercentral-chatbot:latest
     # Deploy to Cloud Run:
     gcloud run deploy sellercentral-chatbot-service \
       --image gcr.io/<YOUR_PROJECT_ID>/sellercentral-chatbot:latest \
       --platform managed --region us-central1 \
       --allow-unauthenticated
     ```  
     Ensure you replace `<YOUR_PROJECT_ID>` with your GCP project ID, and adjust the service name, region, and image tag as needed. After running this, gcloud will output the service URL. In most cases though, the GitHub Actions workflow handles these steps, so manual deployment is only needed if bypassing CI or for quick experiments.

4. **Verifying the Deployment**:  
   Once the GitHub Actions workflow completes (or your manual `gcloud run deploy` finishes), you should verify that the chatbot service is up and running on Cloud Run:
   - **Find Service URL**: The Cloud Run service will have a unique URL. It typically looks like `https://<SERVICE_NAME>-<RANDOM_HASH>-<REGION>.a.run.app`. You can find this URL in the deployment output or by going to the Cloud Run section of the GCP Console and clicking on the service name, where the URL will be listed. 
   - **Health Check**: The chatbot system might have a health-check endpoint (for example, `/health` or `/`) that returns a simple success message. Try accessing it in a web browser or via curl. For instance:  
     ```bash
     curl -X GET https://sellercentral-chatbot-service-xxxxxxxx-uc.a.run.app/health
     ```  
     If there's no dedicated health path, you can curl the root URL (`/`). A successful response (HTTP 200) or a welcome message like "SellerCentral ChatBot is running" indicates the service is deployed.  
   - **Chatbot Query Test**: To truly test functionality, you might have an endpoint like `/chat` or `/query` where you send a chat message and get a response. For example, if the API expects a JSON payload with a user query, you could do:  
     ```bash
     curl -X POST https://sellercentral-chatbot-service-xxxxxxxx-uc.a.run.app/chat \
          -H "Content-Type: application/json" \
          -d '{ "question": "Hello, what can you do?" }'
     ```  
     This should return a JSON response from the chatbot (for example, an answer or greeting). The exact request format depends on how the chatbot API is designed in the code. Check the project documentation or code (perhaps in a README or the source) for the correct endpoint and JSON format.  
   - **Unauthenticated Access**: If you get an HTTP 403 Forbidden, it might mean the service is **not** open to public. In that case, you’d need to obtain an identity token and include it in the curl request’s Authorization header, or adjust the Cloud Run service to allow unauthenticated invocations. (Ensuring `--allow-unauthenticated` at deploy time, as we did above, prevents this issue in a public demo setting.)  
   - **Check Logs**: As a final verification, go to the Cloud Run service in the GCP Console and click on **Logs**. You should see entries for the request you just made (Cloud Run provides request logs, and your application might log details as well). This confirms that the system not only deployed but is actively handling requests.

By following these steps, you will have the SellerCentral-ChatBot-System deployed on Cloud Run and confirmed that it's functional. Future updates can be deployed simply by pushing changes to the repository (triggering the CI/CD workflow again), making the process of maintaining the chatbot very convenient.

## CI/CD Pipeline

The continuous integration/continuous delivery pipeline is implemented with **GitHub Actions**, enabling automated builds, tests, and deployment on every code change. Here’s an overview of the CI/CD setup and how it works:

- **Workflow Configuration**: The repository contains a workflow file (e.g., `.github/workflows/deploy.yml`) that defines the CI/CD process. This YAML file specifies triggers and a series of jobs/steps. For this project, the workflow is triggered on updates to the main branch (for example, on every push to `main` or when a pull request is merged). It may also allow manual triggers for deployment via the GitHub Actions interface if configured with `workflow_dispatch`. The trigger configuration ensures that the latest code is automatically deployed, achieving true continuous delivery.

- **Build and Test Stages**: Once triggered, the workflow runs on a GitHub-provided runner (Ubuntu VM by default). Typical stages in the job include:
  - *Checkout Code*: Uses `actions/checkout@v4` to pull the repository code onto the runner.
  - *Set up Cloud SDK*: Uses the Google Cloud action `google-github-actions/setup-gcloud` to install the gcloud CLI and authenticate. The service account credentials (from the `GCP_SA_KEY` secret) are used here to log in to GCP within the runner environment. After this, `gcloud` commands and other Google Cloud tools can be used.
  - *Build Docker Image*: The workflow builds the Docker image for the chatbot. It might do this with a Docker action or simply by running `docker build` in a script step. This compiles the application and packages it into a container image. If there are tests, this stage could also run unit tests (e.g., if using a Python app, maybe running `pytest` before building or as part of the build).
  - *Push to Registry*: After building, it logs in to Google’s container registry (using stored credentials or the gcloud auth) and pushes the image. The image tag might be `latest` or based on the commit SHA or a version number.
  - *Deploy to Cloud Run*: Finally, the workflow calls `gcloud run deploy` (or uses the `google-github-actions/deploy-cloudrun` action) to update the Cloud Run service with the new image. This step will replace the existing service revision with a new one carrying the updated code. By the end of this step, Cloud Run will serve the new version of the chatbot. The output of this action is often the service URL and confirmation of a successful deployment.

- **Continuous Deployment Behavior**: Thanks to this pipeline, developers do not need to manually intervene for deploying changes. For example, if a developer fixes a bug or adds a new feature to the chatbot and pushes a commit, within a few minutes the GitHub Actions workflow will build and release that change to Cloud Run. This reduces deployment friction and errors since the process is scripted and consistent. It also encourages frequent, incremental updates. If a build or deploy fails (due to a code issue or infrastructure problem), the GitHub Actions UI will show a failure, and the team can address it before it affects the production service.

- **Security and Credentials**: The CI/CD setup keeps sensitive information (like GCP credentials) in GitHub Secrets, not in the code. Only the GitHub Actions runner can access these secrets during a run. This protects the GCP account from unauthorized access. Additionally, using least-privilege principles for the service account (only giving it deploy permissions) ensures the CI/CD pipeline cannot perform unintended operations.

- **Rollback Strategy**: Although not explicitly part of the question, it’s worth noting: Cloud Run retains previous revisions of the service. In case a deployment has issues, one can quickly roll back to the last known good revision via the Cloud Run console or CLI. The CI pipeline could also be configured to only deploy on passing tests or incorporate manual approval for production, depending on how critical the application is. However, for this chatbot, we assume fully automated deployments for speed.

In summary, the CI/CD pipeline uses GitHub Actions to seamlessly integrate code changes with deployment. This follows industry best practices for DevOps, where code commits trigger builds and deployments in a reproducible manner ([From Code to Cloud: GitHub Actions for Cloud Run Deployment | by Azeez | Medium](https://azeezz.medium.com/from-code-to-cloud-github-actions-for-cloud-run-deployment-dc1304573642#:~:text=Github%20Actions%20is%20a%20continuous,with%20a%20Service%20Account%20Key)). The result is that maintaining and updating the SellerCentral-ChatBot-System is efficient and reliable, with minimal downtime and human error.

## Monitoring and Logging

Monitoring the chatbot’s performance and usage is crucial for ensuring reliability. In this project, we implement monitoring primarily through logging. The approach is to log key events from the application and then use those logs to derive metrics. Here's how it works and how you can utilize it:

- **Cloud Run Logging**: Out of the box, Cloud Run streams all logs from the application to **Google Cloud Logging** (formerly Stackdriver Logging). This includes two types of logs: **request logs** (each HTTP request has an entry with response code, latency, etc.) and **application logs** (any `stdout` or `stderr` output from the app) ([Logging and viewing logs in Cloud Run  |  Cloud Run Documentation  |  Google Cloud](https://cloud.google.com/run/docs/logging#:~:text=Cloud%20Run%20has%20two%20types,automatically%20sent%20to%20Cloud%20Logging)). Our chatbot application is instrumented to log specific events:
  - When the chatbot starts handling a new chat session or question, it logs a message like “Chatbot session started” (with perhaps a timestamp or session ID).
  - If an error or exception occurs (for example, if the model fails to generate a response or an internal error happens), the code logs an error message like “Chatbot error: <error details>”.
  - (Optionally, we could log other info such as the user’s question or the response time, but the key metrics of interest are start counts and error counts.)

- **Log-based Metrics in BigQuery**: Instead of using Cloud Monitoring’s custom metrics, we opted to export logs to **BigQuery** for analysis. A logging **sink** is configured in Cloud Logging that matches our chatbot’s logs and routes them to a BigQuery dataset. This means that every time a log entry is written (e.g., "Chatbot session started"), it is also appended as a row in a BigQuery table. Google’s logging service streams the data in small batches efficiently ([View logs routed to BigQuery  |  Cloud Logging  |  Google Cloud](https://cloud.google.com/logging/docs/export/bigquery#:~:text=This%20document%20explains%20how%20you,also%20describes%20the%20%20213)). In BigQuery, the logs can be queried using SQL, which provides a flexible way to calculate metrics over any time period:
  - **Chatbot Started Count**: You can count the number of "start" logs to see how many times the chatbot was invoked. For example, a simple BigQuery SQL query might be:  
    ```sql
    SELECT DATE(timestamp) as date, COUNT(*) as sessions
    FROM `your_project.logging_dataset.chatbot_logs`
    WHERE textPayload CONTAINS "Chatbot session started"
    GROUP BY date
    ORDER BY date;
    ```  
    This would give you daily counts of chatbot sessions started. (The exact field names like `textPayload` or schema depends on how the logs are structured in BigQuery, but generally the message appears in one of the payload fields).
  - **Chatbot Error Count**: Similarly, you can count error logs. For example:  
    ```sql
    SELECT DATE(timestamp) as date, COUNT(*) as errors
    FROM `your_project.logging_dataset.chatbot_logs`
    WHERE textPayload CONTAINS "Chatbot error"
    GROUP BY date
    ORDER BY date;
    ```  
    This yields the number of errors logged each day. If you join or compare the two metrics, you can calculate an error rate (errors per session) as well.

- **Viewing Logs and Metrics**: To inspect logs directly, you have a few options:
  - Use the **Cloud Run Logs** tab in the Google Cloud Console (navigate to Cloud Run service, then Logs). This is handy for recent logs or debugging specific issues.
  - Use **Cloud Logging Logs Explorer** for advanced filtering (you can filter by severity, or search for the text "Chatbot error" etc., across all logs).
  - Use **BigQuery**: go to the BigQuery console, find the dataset (for example, it might be named `chatbot_logs` or part of a logging dataset with your project ID), and you can query it or even just preview the table. BigQuery is particularly useful for aggregating metrics over time as shown in the examples above. Since the logs are stored in BigQuery, you could also connect a dashboard tool (e.g., Google Data Studio/Looker Studio) to visualize these metrics over time, if desired.

- **Alerting (Optional)**: While not explicitly set up in this project, you could create alerts in Cloud Monitoring based on these metrics. For instance, a **logs-based metric** could be defined in Cloud Monitoring to count "Chatbot error" occurrences and trigger an alert if the count exceeds a threshold in a given period. Alternatively, since data is in BigQuery, one could schedule a query or use an external script to monitor and send notifications. Given the scope of this project, we focus on manual monitoring via queries rather than automated alerts.

- **BigQuery Cost Consideration**: Exporting logs to BigQuery has cost implications (storage and query costs). However, for a moderate volume of logs (e.g., a chatbot with light usage), the cost is minimal. Logs in BigQuery allow long-term retention and complex analysis which Cloud Logging alone might limit (Cloud Logging also has retention limits depending on settings). It's a trade-off for the educational scenario to demonstrate custom monitoring. In a real production scenario, one might use Cloud Monitoring dashboards or export logs to a more purpose-built monitoring system if needed.

By reviewing the BigQuery logs, one can determine how frequently the chatbot is used and how stable it is (via error counts). For instance, if the "chatbot started" count suddenly drops to zero on a given day, it might indicate an outage or deployment issue. If the "error count" spikes, it signals something is wrong in responses or system performance. This logging-based monitoring provides a feedback loop to improve the chatbot system over time.

## Local Development and Testing

For development purposes or to run the chatbot locally (outside of Cloud Run), you have a couple of options. This allows you to test changes quickly before pushing to the cloud, or to debug issues in a local environment.

- **Running Locally with Docker**: The easiest way to mirror the Cloud Run environment is to use Docker on your development machine.
  1. Ensure you have Docker installed and the code cloned locally (as described in the Deployment Instructions section).
  2. Build the Docker image locally:  
     ```bash
     docker build -t sellercentral-chatbot:dev .
     ```  
     This will execute the Dockerfile and produce an image named `sellercentral-chatbot:dev` on your machine.
  3. Run a container from the image:  
     ```bash
     docker run -p 8080:8080 --env PORT=8080 sellercentral-chatbot:dev
     ```  
     We map port 8080 of the container to port 8080 of the host. Cloud Run by default will send requests to whatever port is defined in the `$PORT` environment variable (often 8080), so we ensure it's set. If your application expects any other environment variables (for example, API keys or configuration flags), supply them with `--env KEY=value` or by using an `--env-file` pointing to a local `.env` file. For instance, if the chatbot needs `OPENAI_API_KEY` to call an external API, you'd run `docker run -p 8080:8080 -e OPENAI_API_KEY=XYZ sellercentral-chatbot:dev`.
  4. Once the container is running, test it by sending requests from your host machine:  
     ```bash
     curl http://localhost:8080/health
     ```  
     (or the appropriate path, similar to how you would for the deployed version). You should see similar responses locally as you would from the Cloud Run deployment. Logs will print to your terminal where Docker is running, which is useful for debugging. Stop the container with Ctrl+C when done.

- **Running Locally without Docker**: Depending on how the project is structured, you might run the application directly on your host (e.g., via Python or Node). For example, if it's a Python Flask app, you might do `pip install -r requirements.txt` and then `flask run` or `python app.py`. Check the project documentation for a local run script or instructions (some projects have a `make run` or `npm start` command). Keep in mind, replicating the environment exactly might require installing additional system packages or dependencies that the Dockerfile would normally handle. Using Docker as above sidesteps these issues by using the same container environment as production.

- **Testing Changes**: When developing, it's good practice to write unit tests or integration tests for your chatbot logic. If the repository includes tests, you can run them locally (e.g., with `pytest` or `npm test`). This helps ensure your changes haven't broken existing functionality. You can also simulate requests to the chatbot by crafting example JSON inputs and seeing if the responses are as expected.
  
- **Environment Variables and Config**: The chatbot likely uses environment variables for configuration (for example, credentials or settings). In Cloud Run, you can set these in the service configuration (via the deploy command or the Cloud Console). Locally, you should define them too. For local Docker runs, as mentioned, use `--env` flags or a `.env` file. For direct local runs, you might export variables in your shell or use a tool like `direnv`. Always be careful not to hardcode sensitive information in code; use configs so that you can keep them out of version control.

- **Connecting to Cloud Services Locally**: If your chatbot needs to access GCP services (perhaps BigQuery or Cloud Storage for some reason), you can either use local application default credentials (`gcloud auth application-default login` sets up credentials for local use) or service account keys. Alternatively, you might mock those parts during local testing if they are not essential to the chatbot’s core logic.

By following these local setup guidelines, you can iterate on the chatbot quickly. Once you're satisfied with local tests, commit and push your changes to let the CI/CD pipeline deploy them to Cloud Run. Always re-test the deployed version briefly (with curl or through its interface) to make sure everything runs in the cloud environment as it did locally.


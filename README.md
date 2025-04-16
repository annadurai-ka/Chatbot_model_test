# Review of Logging and Production-Readiness Improvements

## ✅ Review Summary
Your project already includes solid practices in logging, environment handling, and modularity. Below are suggestions to **enhance it to production quality**, focusing on the following:

- Structured logging
- Sensitive info masking
- Reusability and config loading
- Monitoring/log forwarding readiness

---

## 🔁 Recommended Updates (Across Files)

### 1. config/config.py — Central Config for Logging
```python
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Set default log format
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger("SellerChatbot")

# Centralized environment variables
HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST")
GCP_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Check required envs
REQUIRED_ENVS = [HF_TOKEN, DEEPSEEK_API_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, GCP_CREDENTIALS]
if not all(REQUIRED_ENVS):
    raise ValueError("Missing required environment variables.")
```

### 2. src/chatbot_model.py — Import and Use `logger`
```python
from config.config import logger, HF_TOKEN, OPENAI_API_KEY, ...
```
Replace:
```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```
With:
```python
# Reuse global logger
from config.config import logger
```

Also: Mask sensitive values (just log token presence):
```python
logger.info("Env loaded: HF_TOKEN: %s, DEEPSEEK_API_KEY: %s", bool(HF_TOKEN), bool(DEEPSEEK_API_KEY))
```

### 3. Use JSON Structured Logs (for GCP Cloud Logging)
Use `jsonlogger`:
```bash
pip install python-json-logger
```
Then in `config.py`:
```python
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger("SellerChatbot")
logger.setLevel(LOG_LEVEL)
logger.addHandler(logHandler)
```

### 4. Dockerfile (Ensure Logs Appear in GCP Logs)
Ensure logs go to stdout:
```dockerfile
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
```

---

## ✅ Good Practices Already Done
- ✅ Modular structure with `chain`, `retriever`, `model`
- ✅ Logs added for major steps (fetching, QA chain, response)
- ✅ Exception handling with `logger.exception()`
- ✅ `requirements.txt` scoped well for LangChain use
- ✅ Cloud Run–compatible Docker setup

---

## ✅ Monitoring Readiness (Future Work)
- Integrate **OpenTelemetry** or **Prometheus** for trace metrics
- Log response time (start/stop time)
- Forward logs to **Cloud Logging** with `LOG_FORMAT` containing `severity`, `service`, etc.

---

Let me know when you want to implement structured metrics/log streaming or alerting setup next! 🚀

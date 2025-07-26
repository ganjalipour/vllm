# OMEGA UI

This is the frontend UI for the OMEGA project, built with Streamlit.

## 🚀 Running the UI with Docker Compose

### 1. Build and Start All Services

From the project root directory (where `docker-compose.yml` is located), run:

```bash
docker-compose up --build ui
```

This will build the UI Docker image and start the UI service (and its dependencies if needed).

- The UI will be available at: [http://localhost:8501](http://localhost:8501)

### 2. Stopping the UI

To stop the UI and other services:

```bash
docker-compose down
```

---

## ⚠️ Configuring `FASTAPI_URL`

The UI needs to communicate with the FastAPI backend. The URL for the backend is set in the code (see `inference_stream.py`) as `FASTAPI_URL`.

### **Why Not Use `localhost`?**
- When running in Docker Compose, each service runs in its own container.
- `localhost` inside the UI container refers to itself, **not** the API container.
- Use the Docker Compose service name (e.g., `api`) as the hostname.

### **How to Set the Backend URL**

#### **Development (Docker Compose)**
- The backend API service is named `api` in `docker-compose.yml`.
- Set the URL to:
  ```
  http://api:8000/chat/streamcompletions
  ```
- This is already set in the code, but for flexibility, you can use an environment variable:

  In `inference_stream.py`:
  ```python
  import os
  FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000/chat/streamcompletions")
  ```

  In `docker-compose.yml` (under the `ui` service):
  ```yaml
  environment:
    - FASTAPI_URL=http://api:8000/chat/streamcompletions
  ```

#### **Production (Non-Docker or Different Network)**
- If the backend is running elsewhere (e.g., on a different server or domain), set the environment variable accordingly:
  ```yaml
  environment:
    - FASTAPI_URL=https://your-backend-domain.com/chat/streamcompletions
  ```
- Or set it at runtime:
  ```bash
  docker run -e FASTAPI_URL=https://your-backend-domain.com/chat/streamcompletions ...
  ```

---

## 🛠️ Local Development (Without Docker)

If you want to run the UI locally (not in Docker):

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the UI:
   ```bash
   streamlit run inference_stream.py
   ```
3. Make sure the backend API is running and set `FASTAPI_URL` in your environment or in the code to `http://localhost:8000/chat/streamcompletions`.

---

## 📄 Summary Table

| Environment                | `FASTAPI_URL` value                          |
|----------------------------|----------------------------------------------|
| Docker Compose (default)   | http://api:8000/chat/streamcompletions             |
| Local (no Docker)          | http://localhost:8000/chat/streamcompletions       |
| Production (custom domain) | https://omega.cat/chat/streamcompletions |

---

For more details, see the main project README or contact the maintainers.

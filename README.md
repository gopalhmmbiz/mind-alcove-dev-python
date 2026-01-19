# MindAlcove – AI Service

MindAlcove – AI Service is a FastAPI-powered backend application designed to deliver AI-driven features for the MindAlcove platform. The service focuses on mental wellness use cases such as AI-powered affirmations, journal suggestions, audio transcriptions, and more.

The project uses LangChain as the AI framework and Google Gemini as the underlying LLM, with uv as the package and environment manager.

---

## Tech Stack

- Language: Python 3.11
- Framework: FastAPI
- AI Framework: LangChain
- LLM Provider: Google Gemini
- Package Manager: uv
- Containerization: Docker
- ASGI Server: Uvicorn

---

## Project Structure (High-Level)

.
├── app/
│   ├── main.py          # FastAPI application entry point
│   ├── api/             # API routes
│   ├── db/              # Database session & models
│   ├── core/            # Config, exceptions, responses
│   └── ...
├── pyproject.toml
├── uv.lock
├── Dockerfile
└── README.md

---

## Health Check

The service exposes a health endpoint for monitoring and uptime checks:

GET /api/health

This endpoint is unauthenticated and intended for container probes, load balancers, and monitoring systems.

---

## Docker Setup & Run Instructions

This project is designed to be run using Docker.

### 1. Clone the Repository

Clone the repository and navigate into the project directory:

git clone https://github.com/MatrixMedia/mindalcove-python-backend.git
cd mindalcove-ai-service

---

### 2. Build the Docker Image

Build the Docker image locally:

docker build -t mindalcove-ai-service .

---

### 3. Run the Container

Start the service using Docker:

docker run -p 8000:8000 mindalcove-ai-service

Once the container is running, the API will be accessible at:

http://localhost:8000

---

### 4. Verify the Service

Verify that the service is running correctly by calling the health endpoint:

curl http://localhost:8000/api/health

Expected response (example):

{
  "status": true,
  "message": "Success",
  "data": {
    "app": "mind-alcove-ai-backend",
    "environment": "development",
    "status": "running"
  }
}

---

## Environment Configuration

The service relies on environment variables for configuration, including:

- Google Gemini API keys
- Database connection settings
- Application secrets

You can pass them using an env file:

docker run --env-file .env mindalcove-ai-service

---

## Notes

- Authentication middleware is applied globally except for /api/health
- The service is intended as an internal backend service
- Async SQLAlchemy is used for database access
- uv is responsible for dependency resolution and execution

---

## License

Proprietary – internal use only.

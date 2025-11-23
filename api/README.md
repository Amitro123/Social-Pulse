# Social Pulse API (FastAPI)

## Install

```bash
pip install fastapi uvicorn[standard] pytest pytest-asyncio httpx python-multipart
```

## Run

```bash
uvicorn api.main:app --reload
```

Open docs at http://localhost:8000/docs

## Test

```bash
pytest -v
```

## Notes
- CORS enabled for all origins by default (configure via env CORS_ORIGINS)
- Expensive operations cached for 5 minutes (CACHE_TTL_SECONDS)
- Simple rate limiter dependency controls QPS
- Endpoints return Pydantic models with validation

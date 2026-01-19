# Antigravity Link Backend

FastAPI-based relay server for Antigravity Link remote control system.

## Features

- JWT authentication
- Device pairing via QR codes
- WebSocket real-time communication
- Command queue with Redis
- File upload/download
- Audit logging
- Rate limiting

## Setup

### Development

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure .env file
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Production

```bash
docker-compose up -d
```

## API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

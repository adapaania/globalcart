# Multi-stage build: build the Vite frontend, then serve it from FastAPI.
# Produces a single container exposing one URL (API + SPA).

# ---- Stage 1: build frontend ----
FROM node:20-alpine AS frontend
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: backend + static frontend ----
FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Copy the built SPA into the location main.py serves from.
COPY --from=frontend /fe/dist ./static

EXPOSE 8000

# Railway/most PaaS inject $PORT; default to 8000 locally.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

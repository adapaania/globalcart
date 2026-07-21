FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Week 2/3: switch to `uvicorn main:app` once the API is implemented.
CMD ["python", "main.py"]

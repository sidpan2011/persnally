FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt /app/root-requirements.txt
COPY api/requirements.txt /app/api-requirements.txt
RUN pip install --no-cache-dir -r root-requirements.txt -r api-requirements.txt

# Copy source code
COPY src/ /app/src/
COPY api/ /app/api/
COPY templates/ /app/templates/
COPY data_sources/ /app/data_sources/

WORKDIR /app/api

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

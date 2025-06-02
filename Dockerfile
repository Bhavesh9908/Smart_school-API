FROM python:3.11-slim

# Install only essential system dependencies (no recommended extras)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender1 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Use .dockerignore to exclude unnecessary files (see below)
COPY requirements.txt .

# Install pip packages with CPU-only torch and minimal cache
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch==2.2.1+cpu -f https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# Cleanup extra files
RUN find /usr/local/lib/python3.11 -name '*.pyc' -delete \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -exec rm -rf {} +

# Copy application code
COPY . .

# Expose app port
EXPOSE 5000

# Start the server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

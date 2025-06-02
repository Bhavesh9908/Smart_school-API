FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV YOLO_CONFIG_DIR=/tmp/ultralytics_config

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender1 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create writable config directory for Ultralytics
RUN mkdir -p $YOLO_CONFIG_DIR

WORKDIR /app

# Copy requirements and install packages
COPY requirements.txt .

# Install PyTorch CPU version and dependencies
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch==2.2.1+cpu -f https://download.pytorch.org/whl/torch_stable.html \
 && pip install --no-cache-dir -r requirements.txt

# Optional: Clean up bytecode files to reduce image size
RUN find /usr/local/lib/python3.11 -name '*.pyc' -delete \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -exec rm -r {} +

# Copy the rest of the app
COPY . .

EXPOSE 5000

# Run Gunicorn with Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

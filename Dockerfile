# Use slim and lightweight base
FROM python:3.11-slim-buster

# Install system dependencies for OpenCV and other tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender1 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file only (for layer caching)
COPY requirements.txt .

# Upgrade pip and install torch separately using the official link
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch==2.2.1+cpu -f https://download.pytorch.org/whl/torch_stable.html \
 && pip cache purge \
 && rm -rf ~/.cache/pip

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt \
 && pip cache purge \
 && rm -rf ~/.cache/pip

# Copy the rest of the application code
COPY . .

# Clean up Python cache files
RUN find /usr/local/lib/python3.11 -name '*.pyc' -delete \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -exec rm -r {} +

# Expose the port
EXPOSE 5000

# Start the app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

FROM python:3.11-slim

# Environment settings to prevent .pyc files and enable stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements to cache Docker layer
COPY requirements.txt .

# Upgrade pip and install torch CPU
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.0.1+cpu -f https://download.pytorch.org/whl/torch_stable.html && \
    pip install --no-cache-dir \
        flask==2.2.5 \
        werkzeug==2.2.3 \
        gunicorn==20.1.0 \
        cloudinary==1.34.0 \
        Pillow==9.5.0 \
        numpy==1.24.3 \
        opencv-python-headless==4.7.0.72 && \
    pip install --no-cache-dir ultralytics  # ← Do NOT pin version unless absolutely required

# Copy rest of the application files
COPY . .

# Expose the Flask app port
EXPOSE 5000

# Start the app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

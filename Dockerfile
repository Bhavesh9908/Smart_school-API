# Use valid official PyTorch image (CPU-only)
FROM pytorch/pytorch:2.0.0-cpu

# Prevent .pyc and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required for opencv-python-headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files into the container
COPY . .

# Expose port (Flask default)
EXPOSE 5000

# Command to run app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

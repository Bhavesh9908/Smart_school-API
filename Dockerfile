FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install torch (CPU only)
RUN pip install --no-cache-dir torch==2.0.1+cpu -f https://download.pytorch.org/whl/torch_stable.html

# Install remaining Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir flask==2.2.5 werkzeug==2.2.3 gunicorn==20.1.0 cloudinary==1.34.0 Pillow==9.5.0 numpy==1.24.3 opencv-python-headless==4.7.0.72 ultralytics==8.0.20

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

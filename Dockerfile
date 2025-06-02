FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender1 \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install PyTorch and torchvision from official source
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch==2.2.1+cpu torchvision==0.17.1+cpu \
      -f https://download.pytorch.org/whl/cpu/torch_stable.html \
 && pip install --no-cache-dir -r requirements.txt \
 && find /usr/local/lib/python3.11 -name '*.pyc' -delete \
 && find /usr/local/lib/python3.11 -name '__pycache__' -type d -exec rm -r {} +

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

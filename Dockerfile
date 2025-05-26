FROM python:3.11-slim as base

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libglib2.0-0 \
    libgl1 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose the port
EXPOSE 5000

# Use gunicorn to run the Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

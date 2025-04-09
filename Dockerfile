FROM python:3.11-slim

# Install system dependencies including libGL
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy app files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose the Flask port
EXPOSE 5000

# Start the Flask app using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

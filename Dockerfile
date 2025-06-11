# Use Python 3.10 as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create directories for output, logs, and results
RUN mkdir -p output logs results

# Entry point
ENTRYPOINT ["python", "main.py"]

# Default command (can be overridden)
CMD ["--output", "results"]


# docker run hackathon-review-system --project ai-health-assistant  
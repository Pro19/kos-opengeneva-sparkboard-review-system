FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p output logs results
COPY . .

RUN pip install --no-cache-dir -r requirements.txt


ENTRYPOINT ["python", "-m", "src.cli.main"]

CMD ["--output", "results"]

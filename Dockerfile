FROM python:3.11-slim

WORKDIR /app

# Install system deps for Pillow and wkhtmltoimage
RUN apt-get update && apt-get install -y --no-install-recommends \
    wkhtmltopdf \
    fonts-inter \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: Run scheduler
CMD ["python", "main.py"]

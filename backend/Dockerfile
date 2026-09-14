FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for PyMuPDF, asyncpg)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Default port (platforms like Render/Railway inject $PORT at runtime)
ENV PORT=8000

# Expose the port
EXPOSE ${PORT}

# Start Uvicorn — uses $PORT so it works on Render, Railway, Fly.io
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}

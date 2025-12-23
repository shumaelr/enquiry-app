FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create data directories with sample files from the repo
RUN mkdir -p /app/data/BOQ /app/data/Sizing /app/data/SLD

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WATCH_DIRECTORY=/app/data
ENV PORT=8080

# Run the application
CMD ["python", "web_viewer.py"]

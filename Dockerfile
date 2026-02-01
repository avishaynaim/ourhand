FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY *.py .
COPY templates/ templates/
COPY static/ static/

# Expose web dashboard port
EXPOSE 5000

# Health check (uses /ping which doesn't require auth)
# Using python instead of curl since slim image doesn't include curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/ping', timeout=5)" || exit 1

CMD ["python", "app.py"]

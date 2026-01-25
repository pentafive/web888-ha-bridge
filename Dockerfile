FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY web888-ha-bridge.py .
COPY web888_client.py .

# Run the bridge
CMD ["python", "-u", "web888-ha-bridge.py"]

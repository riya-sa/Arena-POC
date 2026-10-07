# FROM python:3.11-slim

# WORKDIR /app

# # Install system dependencies
# # RUN apt-get update && apt-get install -y \
# #     gcc \
# #     postgresql-client \
# #     && rm -rf /var/lib/apt/lists/*

# # Copy requirements
# COPY requirements.txt .

# # Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy application code
# COPY . .

# # Create necessary directories
# RUN mkdir -p logs

# # Run migrations and start app (can be overridden in compose)
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]



# Starts from a pre-built image that contains Python 3.11
FROM nikolaik/python-nodejs:python3.11-nodejs20-slim

# Copy the JDK 21 binaries from the official Temurin image straight into this container
COPY --from=eclipse-temurin:21-jdk /opt/java/openjdk /opt/java/openjdk
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

WORKDIR /app

# ALL APT-GET LAYERS REMOVED TO BYPASS WINDOWS DOCKER NETWORK FREEZE

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs

# Run migrations and start app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

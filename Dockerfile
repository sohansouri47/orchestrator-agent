# Use the official Python image as a base
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv using pip
RUN pip3 install --no-cache-dir uv

# Copy your application files
COPY . .

# Set the environment variable for uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install project dependencies using uv
RUN uv sync --frozen --no-install-project --no-dev

# Expose the application port
EXPOSE 10000

# Command to run your application
CMD ["uv", "run", "python3", "-m", "src.agents.OrchestratorAgent"]

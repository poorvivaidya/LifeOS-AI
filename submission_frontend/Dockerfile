FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Enable python bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Install dependencies using pyproject.toml
COPY pyproject.toml ./
RUN uv pip install --system -r pyproject.toml

# Copy application source code
COPY . .

# Expose port 8080
EXPOSE 8080

# Start FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

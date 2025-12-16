FROM python:3.12

WORKDIR /code

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy uv files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000 5678

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Use uv to run the application with debugging
#CMD ["uv", "run", "python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Use uv to run the application in production
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
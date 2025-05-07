FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry install --no-root

COPY . .

CMD ["poetry", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "10000"]

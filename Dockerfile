# ------------ BUILD STAGE ------------

FROM python:3.10-slim as builder

WORKDIR /app

# Cài dependencies hệ thống
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Cài poetry
RUN pip install poetry==1.8.2

# Cấu hình poetry không tạo virtualenv riêng
ENV PIP_NO_BUILD_ISOLATION=1

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy source code
COPY . .

# ------------ RUNTIME STAGE ------------

FROM python:3.10-slim

WORKDIR /app

# Cài gói hệ thống cần thiết cho psycopg2 runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

EXPOSE 8000

CMD ["python", "app.py"]

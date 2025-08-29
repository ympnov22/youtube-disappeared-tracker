FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml poetry.lock* requirements*.txt* /app/
RUN pip install --no-cache-dir -U pip && \
    if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

COPY . /app

ENV PORT=8080
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system app \
    && adduser --system --ingroup app app

COPY app ./app
COPY run_api.py .

RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["uvicorn", "app.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
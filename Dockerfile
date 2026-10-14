FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home appuser
COPY app ./app
COPY web ./web
RUN mkdir -p /app/data && chown -R appuser:appuser /app
USER appuser
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT}"]


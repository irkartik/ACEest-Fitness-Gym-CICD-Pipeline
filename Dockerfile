FROM python:3.12-slim

WORKDIR /workspace

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY tests/ tests/

EXPOSE 5000

CMD ["python", "app/main.py"]

FROM python:3.12-slim

WORKDIR /workspace

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY tests/ tests/

ARG GIT_COMMIT=unknown
ARG BUILD_NUMBER=unknown
ENV GIT_COMMIT=${GIT_COMMIT}
ENV BUILD_NUMBER=${BUILD_NUMBER}

EXPOSE 5000

CMD ["python", "app/main.py"]

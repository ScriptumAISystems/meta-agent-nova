FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /tmp/base-requirements.txt
RUN pip install --no-cache-dir -r /tmp/base-requirements.txt

COPY deploy/automation/bridge/requirements.txt /tmp/bridge-requirements.txt
RUN pip install --no-cache-dir -r /tmp/bridge-requirements.txt

COPY . /app

CMD ["uvicorn", "deploy.automation.bridge.app:app", "--host", "0.0.0.0", "--port", "8080"]

FROM python:3.11-bookworm

WORKDIR /app

COPY requirements.txt .

# 安裝虛擬環境 + 套件
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --prefer-binary -r requirements.txt

ENV PATH="/opt/venv/bin:$PATH"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" "--reload"]

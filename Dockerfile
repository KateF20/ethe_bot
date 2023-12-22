FROM python:3.10-slim

WORKDIR /app

ENV PYTHONPATH /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

COPY config/abi.json .

CMD ["python3", "-u", "/app/bot/bot.py"]

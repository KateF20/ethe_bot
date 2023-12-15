FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

COPY config/abi.json .

CMD ["python3", "-u", "/app/bot/ethe_bot.py"]
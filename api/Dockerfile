FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl

WORKDIR /app

COPY flask-app.py /app/

RUN pip install --no-cache-dir flask

EXPOSE 5000

CMD ["python", "/app/flask-app.py"]

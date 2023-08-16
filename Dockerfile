FROM python:3.10-slim-buster
COPY . .
WORKDIR .
RUN python -m pip install -r requirements.txt && apt-get update && apt-get install sqlite3

CMD ["python", "main.py"]
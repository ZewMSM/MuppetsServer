FROM python:3.12-slim-bullseye

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app
CMD ["python", "main.py"]
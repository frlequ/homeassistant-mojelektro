FROM python:3.9-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

COPY ./custom_components/mojelektro /app
COPY ./requirements.txt /app

WORKDIR /app
RUN pip install -r requirements.txt

CMD tail -f /dev/null


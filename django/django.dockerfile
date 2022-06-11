FROM python:3.10

WORKDIR /usr/app/src

RUN pip install --no-cache-dir daphne

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY . .

RUN HOSTNAME=unused DEBUG=no SECRET=unused python manage.py makemigrations && HOSTNAME=unused DEBUG=no SECRET=unused python manage.py migrate

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "quizsite.asgi:application"]
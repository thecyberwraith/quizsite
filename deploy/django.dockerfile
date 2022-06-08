FROM python:3.10

WORKDIR /usr/app/src

RUN pip install --no-cache-dir daphne

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
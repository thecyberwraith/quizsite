FROM python:3.10 AS base

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt
RUN useradd -m djangoapp

FROM base AS dev

COPY requirements-dev.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

USER djangoapp:djangoapp
WORKDIR /workspace


FROM base AS projectloaded

USER djangoapp:djangoapp
WORKDIR /usr/app/src
COPY ./src .


FROM projectloaded AS debug

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


FROM projectloaded AS prod

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir daphne

RUN python manage.py makemigrations && python manage.py migrate

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "quizsite.asgi:application"]


FROM projectloaded AS staticsrc

RUN python manage.py collectstatic --no-input


FROM nginx AS nginx

COPY --from=staticsrc /usr/app/src/static /usr/share/nginx/html/static
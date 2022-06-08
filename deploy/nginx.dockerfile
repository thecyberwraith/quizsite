FROM python:3.10 AS staticsrc

WORKDIR /usr/app/src

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --no-input

FROM nginx

COPY --from=staticsrc /usr/app/src/static /usr/share/nginx/html/static
COPY ./configuration/nginx.conf /etc/nginx/conf.d/default.conf
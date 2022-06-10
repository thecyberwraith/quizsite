FROM python:3.10 AS staticsrc

WORKDIR /usr/app/src

COPY ./django/requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY ./django/ .

RUN HOSTNAME=unused DEBUG=unused SECRET=unused python manage.py collectstatic --no-input

FROM nginx

COPY --from=staticsrc /usr/app/src/static /usr/share/nginx/html/static
COPY ./nginx.conf /etc/nginx/templates/default.conf.template
COPY ./certs /etc/nginx/certs
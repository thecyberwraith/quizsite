# Quiz Site

This is intended to be a little site that teachers can use to present Jeopardy style quizzes to their students. But, eventually, it will be fully depoloyable on your own domain!

## Development Setup

This version of QuizSite is build on Python3.10 with the Django library. To get this running, you should:

1) Clone this repository
2) In VSCode, open using a remote container (specified in .devcontainer)
3) Run `python manage.py makemigrations && python manage.py migrate`
4) Boot up the development server by running `python manage.py runserver`

Note that, out of the box, the Docker commands will not work in the development container. However, if you want to just run this on your own laptop, this should work well enough.

## Using Quizzes

### Creating a Quiz

First, you need a superuser in the Django app framework. If you haven't already, run `python manage.py createsuperuser` and follow the directions. Afterwards, run the server and load the admin page at [localhost:8000/admin](localhost:8000/admin). After logging in with your super user account, you can create the quizzes you need.

1) Create a Quiz Model with the name you want.
2) Create all the Category Models associated to your quiz.
3) Create Question Models that each associates to a Category Model.

### Using an Open Quiz

By swapping out the `db.sqlite3` file, you can instantly use quizzes that others have created. In the `sample_quizzes` folder, find all the created quizzes. For practice, try loading the `Example` quiz set.

## Deploying with Docker

If you have Docker installed, then you can depoly this project with it. First, you need the following configurations set.

* In a folder named `certs` at the root of this project, place a `fullchain.pem` and `privkey.pem` for your https certificates.
* In the root directory, create a file name `.env` which holds the following variables:
    * HOSTNAME - The hostname that the service should respond to (should match your certificates)
    * DEBUG - Whether to use debug services in Django.
    * SECRET - The secret key to use for encryption for Django.
    * DATABASE_FILE - Since I use a simple sqlite3 database, persist data by mounting the file from your system into the application! If you don't have the file already, one is generated in the image. NOTE - you may need to manually make migrations on externally persisted database files.

Afterwards, run `docker compose build --pull && docker compose up` to boot up the service. It defaults to port `8080` on the machine. If you want to utilize this service with a self signed certificate, run the command 

`openssl req -x509 -nodes -out ./certs/fullchain.pem -keyout ./certs/privkey.pem`

which will generate self signed certificates.
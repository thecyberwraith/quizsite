# Quiz Site

This is intended to be a little site that teachers can use to present Jeopardy style quizzes to their students. But, eventually, it will be fully depoloyable on your own domain!

## Environment Setup

The preferred method for setting up the project is using VSCode with the VSCode Remote Containers plugin, which assumes you have Docker installed on your machine. Otherwise, you can manually handle the python installation with packages.

### Docker Method

1) Clone this repository
2) In VSCode, open using a remote container (needs the VSCode Remote Containers plugin and Docker installed)
3) Run the task `Setup Database`. This prompts you to create a super user AND WILL DELETE ANY PREVIOUS DATABASE.
4) Boot up the development server by running task `Run Server`

### Manual Method
Assuming Python3.10 is installed on your system, do the following. Use of a virtual environment is optional.

1) Clone this repository
2) Run `pip install -r requirements.txt`
3) Optionally, run `pip install -r requirements-dev.txt` if you want tests to pass.
4) In the `src` directory, run the following commands. These commands should only need to be run once, or after a major update to the project.
    1) `python manage.py createsuperuser`
    2) `python manage.py makemigrations`
    3) `python manage.py migrate`
5) Finally, to run/rerun the server, run `python manage.py runserver` from the `src` directory.

## Using Quizzes

### Creating a Quiz

First, you need a superuser in the Django app framework. If you haven't already, run `python manage.py createsuperuser` and follow the directions. Afterwards, run the server and load the admin page at [localhost:8000/admin](localhost:8000/admin). After logging in with your super user account, you can create the quizzes you need.

1) Create a Quiz Model with the name you want.
2) Create all the Category Models associated to your quiz.
3) Create Question Models that each associates to a Category Model.


### Using a Quiz

The proect homepage should list quizzes that uses can launch. The creator of a quiz can also host their quizzes interactively. This assumes you are logged in as the creator. As of this writing, logins can only happen through the admin interface above.

## Server Configuration

The server allows a few customizations that can be changed by an environment variable. If using Docker, you may put your values in a `.env` file or manually add a `-f other_compose_file.yml` that overrides your customizations.

* SERVER_HOST_NAME - The hostname that the service should respond to (should match your certificates) including the protocol (`http://` or `https://`). The default is `http://localhost`.
* DEBUG - Whether to use debug services in Django and set log level to DEBUG. Default is `True`.
* SECRET - The secret key to use for encryption for Django. Default is `notasecret`

## Deploying with Docker

This project provides a simple deployment using multiple docker compose files. For example, by calling `docker compose -f docker-compose.yml -f docker-compose-qa.yml`, you are configuring the quality assurance deployment which uses a production environment and automatically deploys an SSL enabled Nginx server to handle static files and default routing, assuming you provide a viable certificate.

* CERT_FILE - The https certificate file for the internal nginx instance.
* CERT_KEY - The private key file for the https certiciate.

To generate a self-signed certificate for local SSL, run the command below.

`openssl req -x509 -nodes -out ./certs/fullchain.pem -keyout ./certs/privkey.pem`

In short, after specifying those options, the following commands will get a minimally viable production server running.

* `docker compose -f docker-compose.yml -f docker-compose-qa.yml build`
* `docker compose -f docker-compose.yml -f docker-compose-qa.yml up -d`

Then visit the `SERVER_HOST_NAME` you configured and it should all work! You can customize the variables (such as choosing a real secret and setting `DEBUG` to false) as you see fit.
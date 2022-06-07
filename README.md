# Quiz Site

This is intended to be a little site that teachers can use to present Jeopardy style quizzes to their students.

## Development Setup

This version of QuizSite is build on Python3.10 with the Django library. To get this running, you should:

1) Clone this repository
2) In VSCode, open using a remote container (specified in .devcontainer)
3) Run `python manage.py makemigrations && python manage.py migrate`
4) Boot up the server by running `python manage.py runserver`

## Creating a Quiz

First, you need a superuser in the Django app framework. If you haven't already, run `python manage.py createsuperuser` and follow the directions. Afterwards, run the server and load the admin page at [localhost:8000/admin](localhost:8000/admin). After logging in with your super user account, you can create the quizzes you need.

1) Create a Quiz Model with the name you want.
2) Create all the Category Models associated to your quiz.
3) Create Question Models that each associates to a Category Model.

## Using an Open Quiz

By swapping out the `db.sqlite3` file, you can instantly use quizzes that others have created. In the `sample_quizzes` folder, find all the created quizzes. For practice, try loading the `Example` quiz set.

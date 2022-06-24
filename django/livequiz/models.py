from enum import Enum
from json import dumps, loads
from string import ascii_uppercase, digits

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.db import models, DatabaseError

from quiz.models import QuestionModel, QuizModel

from livequiz.responses import get_current_quiz_view_message

SLUG_SIZE = 8
ALLOWED_CHARS = ascii_uppercase + digits

UNIQUE_RETRIES = 5


def json_property(field_name):
    '''Creates a property the encodes and decodes the field_name string object into a dict using JSON'''

    def get_property(self):
        return loads(getattr(self, field_name))

    def set_property(self, value):
        setattr(self, field_name, dumps(value, separators=(',', ':')))

    return property(fget=get_property, fset=set_property)


def generate_random_slug():
    '''Generates a random string of captial letters and numbers.'''
    return get_random_string(
        length=SLUG_SIZE,
        allowed_chars=ALLOWED_CHARS
    )


class LiveQuizView(Enum):
    '''The possible views that a live quiz can populate.'''
    QUIZ_BOARD = 'quiz_board'
    QUESTION = 'question'
    ANSWER = 'answer'


class LiveQuizManager(models.Manager):
    def create_for_quiz(self, quiz_id: int):
        '''Creates a live quiz for this particular quiz, and generates a unique code.'''
        quiz = QuizModel.objects.get(id=quiz_id)
        code = generate_random_slug()
        for _ in range(UNIQUE_RETRIES):
            try:
                self.get(code=code)
                code = generate_random_slug()
            except LiveQuizModel.DoesNotExist:
                model = LiveQuizModel.objects.create(
                    code=code,
                    quiz=quiz
                )
                model.set_view(LiveQuizView.QUIZ_BOARD)
                return model

        raise DatabaseError(
            f'Failed to create unique code for LiveQuiz within {UNIQUE_RETRIES} tries.'
        )

    def owned_by_user(self, user: User):
        '''Returns a list of live quizzes whose backing quiz is owned by a user.'''
        if not user.is_authenticated:
            return []

        return self.filter(quiz__owner=user)

    def delete(self, quiz_code: str):
        '''Sends a signal to the quizzes channel group that this quiz has been deleted.'''
        livequiz = self.get(code=quiz_code)
        async_to_sync(get_channel_layer().group_send)(
            livequiz.group_name,
            {
                'type': 'quiz.terminated'
            }
        )
        livequiz.delete()


class LiveQuizModel(models.Model):
    '''
    Represents a quiz that is currently being hosted. Multiple host instances
    can be hosting the same quiz. The primary interface should be the register_for_quiz
    and unregister_for_quiz methods, which handle model creation and destruction. The
    register method returns a copy of the objects.
    '''
    objects = LiveQuizManager()

    code = models.SlugField(
        max_length=SLUG_SIZE,
        db_index=True,
        primary_key=True
    )

    quiz = models.ForeignKey(
        to=QuizModel,
        on_delete=models.CASCADE,
        null=False
    )

    start_time = models.DateTimeField(
        auto_now_add=True
    )

    last_view_command_raw = models.CharField(
        max_length=512,
        null=True
    )

    last_view_command = json_property('last_view_command_raw')

    answered_questions_raw = models.CharField(
        max_length=512,
        default='[]'
    )

    answered_questions = json_property('answered_questions_raw')

    player_data_raw = models.CharField(
        max_length=512,
        default='{}'
    )

    player_data = json_property('player_data_raw')

    @property
    def group_name(self):
        '''Returns the unique channels group_name for this quiz.'''
        return f'livequiz_group_{self.code}'

    def set_view(self, view: LiveQuizView, question=None):
        '''
        Generates a JSON state for the specified view and saves it in this instances.

        Returns the JSON for the generated view.
        '''
        view_data = {}
        match view:
            case LiveQuizView.QUIZ_BOARD:
                answered = self.answered_questions
                for category in self.quiz.categories.all():
                    cat_key = category.name
                    view_data[cat_key] = []

                    for question in category.questions.all():
                        if question.pk in answered:
                            view_data[cat_key].append(None)
                        else:
                            view_data[cat_key].append({
                                'id': question.pk,
                                'value': question.value
                            })
            case LiveQuizView.QUESTION:
                question = QuestionModel.objects.get(pk=question)
                view_data = {
                    'id': question.pk,
                    'text': question.question_text
                }
            case LiveQuizView.ANSWER:
                question = QuestionModel.objects.get(pk=question)
                view_data = {
                    'id': question.pk,
                    'text': question.question_text,
                    'answer': question.solution_text
                }
            case _:
                raise Exception(f'Not a valid view from LiveQuizView: {view}')

        self.last_view_command = get_current_quiz_view_message(
            view.value, view_data)

        self.save()

        return self.last_view_command


class LiveQuizParticipant(models.Model):
    socket_name = models.CharField(
        max_length=256,
        unique=True
    )
    name = models.CharField(
        max_length=128
    )
    score = models.IntegerField(
        default=0
    )
    quiz = models.ForeignKey(
        to=LiveQuizModel,
        on_delete=models.CASCADE,
        related_name='participants'
    )

    @staticmethod
    def register_participant(quiz_code, name, socket_name, old_socket_name=None):
        '''
        Called when a participant is added to the game. If they want to reconnect
        to an already existing participant, the old_socket_name must point to an
        already existing participant. Otherwise, the participant is created.
        '''
        quiz = LiveQuizModel.objects.get(quiz_code=quiz_code)
        LiveQuizParticipant.objects.update_or_create(
            defaults={
                'name': name,
                'socket_name': socket_name,
                'quiz': quiz
            },
            socket_name=old_socket_name
        )

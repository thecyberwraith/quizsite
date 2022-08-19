from dataclasses import dataclass
from enum import Enum
from json import dumps, loads
from string import ascii_uppercase, digits

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.db import models, DatabaseError
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from livequiz.responses import get_current_quiz_view_message

SLUG_SIZE = 8
ALLOWED_CHARS = ascii_uppercase + digits

UNIQUE_RETRIES = 5


@dataclass
class QuizData:
    '''
    A representation of data for a live quiz. Each category has
    a name that maps to a tuple of questions. Each question provides
    a point value, a question string, and an answer string.
    '''
    name: str
    categories: dict[str, tuple[tuple[int, str, str]]]


class ParticipantManager(models.Manager):
    '''Fancy participant manipulations.'''

    def register_socket(self, quiz, new_socket_name, old_socket_name):
        '''
        Called when a participant is added to the game. If they want to reconnect
        to an already existing participant, the old_socket_name must point to an
        already existing participant. Otherwise, the participant is created.
        '''
        obj, _ = LiveQuizParticipant.objects.update_or_create(
            socket_name=old_socket_name,
            defaults={
                'socket_name': new_socket_name,
                'quiz': quiz
            }
        )

        return obj


class LiveQuizParticipant(models.Model):
    '''Someone playing the game!'''
    objects = ParticipantManager()

    socket_name = models.CharField(
        max_length=256,
        unique=True
    )

    name = models.CharField(
        max_length=128,
        default='Anonymous'
    )

    score = models.IntegerField(
        default=0
    )

    quiz = models.ForeignKey(
        to='LiveQuizModel',
        on_delete=models.CASCADE,
        related_name='participants'
    )


class BuzzEvent(models.Model):
    '''Someone is supposed to be buzzing in!'''

    player = models.ForeignKey(
        to=LiveQuizParticipant,
        on_delete=models.SET_NULL,
        default=None,
        null=True,
        related_name='+'  # No reference from player
    )

    start = models.DateTimeField(auto_now_add=True)


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
    '''Interface for Live Quiz specific management.'''
    def create_for_quiz(self, host, quiz_data: QuizData):
        '''Creates a live quiz for this particular quiz, and generates a unique code.'''
        code = generate_random_slug()
        for _ in range(UNIQUE_RETRIES):
            try:
                self.get(code=code)
                code = generate_random_slug()
            except LiveQuizModel.DoesNotExist:
                quiz = LiveQuizModel.objects.create(code=code, host=host, name=quiz_data.name)
                for category_name in quiz_data.categories:
                    category = quiz.categories.create(name=category_name)

                    for value, question, answer in quiz_data.categories[category_name]:
                        category.questions.create(
                            value=value,
                            question=question,
                            answer=answer
                        )
                quiz.set_view(LiveQuizView.QUIZ_BOARD)
                quiz.save()
                return quiz

        raise DatabaseError(
            f'Failed to create unique code for LiveQuiz within {UNIQUE_RETRIES} tries.'
        )

    def owned_by_user(self, user: User):
        '''Returns a list of live quizzes whose backing quiz is owned by a user.'''
        if not user.is_authenticated:
            return []

        return self.filter(host=user)


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

    name = models.CharField(
        max_length=256
    )

    host = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='+'
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
        max_length=2048,
        default='{}'
    )

    player_data = json_property('player_data_raw')

    buzz_event = models.OneToOneField(
        to=BuzzEvent,
        on_delete=models.SET_NULL,
        null=True
    )

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
                for category in self.categories.all():
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
                question = LiveQuizQuestion.objects.get(pk=question)
                view_data = {
                    'id': question.pk,
                    'text': question.question
                }
            case LiveQuizView.ANSWER:
                question = LiveQuizQuestion.objects.get(pk=question)
                view_data = {
                    'id': question.pk,
                    'text': question.question,
                    'answer': question.answer
                }
            case _:
                raise Exception(f'Not a valid view from LiveQuizView: {view}')

        self.last_view_command = get_current_quiz_view_message(
            view.value, view_data)

        self.save()

        return self.last_view_command
    

@receiver(pre_delete, sender=LiveQuizModel)
def on_delete_livequiz(**kwargs):
    '''Sends a signal to the quizzes channel group that this quiz has been deleted.'''
    async_to_sync(get_channel_layer().group_send)(
        kwargs['instance'].group_name,
        {
            'type': 'quiz.terminated'
        }
    )


class LiveQuizCategory(models.Model):
    '''A category of questions.'''
    name = models.CharField(max_length=128)
    quiz = models.ForeignKey(
        to=LiveQuizModel,
        on_delete=models.CASCADE,
        related_name='categories'
    )


class LiveQuizQuestion(models.Model):
    '''A simple question/answer with a value.'''
    value = models.IntegerField(default=100)
    question = models.TextField(max_length=512)
    answer = models.TextField(max_length=512)
    category = models.ForeignKey(
        to=LiveQuizCategory,
        on_delete=models.CASCADE,
        related_name='questions'
    )

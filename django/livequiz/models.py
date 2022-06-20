from string import ascii_uppercase, digits

from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.db import models, IntegrityError, DatabaseError

from quiz.models import QuizModel

SLUG_SIZE = 8
ALLOWED_CHARS = ascii_uppercase + digits

UNIQUE_RETRIES = 5


def generate_random_slug():
    return get_random_string(
        length=SLUG_SIZE,
        allowed_chars=ALLOWED_CHARS
    )


class LiveQuizModel(models.Model):
    '''
    Represents a quiz that is currently being hosted. Multiple host instances
    can be hosting the same quiz. The primary interface should be the register_for_quiz
    and unregister_for_quiz methods, which handle model creation and destruction. The
    register method returns a copy of the objects.
    '''
    code = models.SlugField(
        max_length=SLUG_SIZE,
        db_index=True,
        primary_key=True
    )

    quiz = models.ForeignKey(
        to=QuizModel,
        on_delete=models.DO_NOTHING,
        null=False
    )

    start_time = models.DateTimeField(
        auto_now_add=True
    )

    last_view_command = models.CharField(
        max_length=512,
        null=True

    )

    @property
    def group_name(self):
        '''Returns the unique channels group_name for this quiz.'''
        return f'livequiz_group_{self.code}'

    @staticmethod
    def create_for_quiz(quiz_id: int):
        '''Creates a live quiz for this particular quiz, and generates a unique code.'''
        quiz = QuizModel.objects.get(id=quiz_id)
        code = generate_random_slug()
        for _ in range(UNIQUE_RETRIES):
            try:
                LiveQuizModel.objects.get(code=code)
                code = generate_random_slug()
            except LiveQuizModel.DoesNotExist:
                return LiveQuizModel.objects.create(
                    code=code,
                    quiz=quiz
                )

        raise DatabaseError(
            f'Failed to create unique code for LiveQuiz within {UNIQUE_RETRIES} tries.'
        )
    
    @staticmethod
    def get_owned_by_user(user: User):
        if not user.is_authenticated:
            return []
        
        return LiveQuizModel.objects.filter(quiz__owner=user)


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

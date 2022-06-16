from string import ascii_uppercase, digits

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

    registered_hosts = models.IntegerField(default=1)

    start_time = models.DateTimeField(
        auto_now_add=True
    )

    last_view_command = models.CharField(
        max_length=512,
        null=True

    )

    last_view_data = models.CharField(
        max_length=1024,
        null=True
    )

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
    def register_for_quiz(quiz_id: int):
        '''
        Signifies that a host is registering to manage this quiz. If a hosted quiz already exists,
        we increment the registered hosts count. Otherwise, we create a new live quiz entry.

        Returns the created/retrieved live quiz.
        '''

        try:
            quiz = LiveQuizModel.objects.get(quiz__id=quiz_id)
            quiz.registered_hosts += 1
            quiz.save()
            return quiz
        except LiveQuizModel.DoesNotExist:
            pass

        return LiveQuizModel.create_for_quiz(quiz_id=quiz_id)

    @staticmethod
    def unregister_for_quiz(quiz_id: int):
        '''
        Signifies that a host is unregistering from managing the quiz. If no more hosts are
        managing, then the live quiz entry is deleted.

        Returns boolean - True if the quiz is no longer managed.
        '''
        quiz = LiveQuizModel.objects.get(quiz__id=quiz_id)
        quiz.registered_hosts -= 1

        if quiz.registered_hosts <= 0:
            quiz.delete()
            return True

        quiz.save()
        return False

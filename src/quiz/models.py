from django.db import models
from django.contrib.auth.models import User


class QuizModel(models.Model):
    name = models.CharField(max_length=100, unique=True,
                            blank=False, null=False)

    self_quiz_option = models.BooleanField(default=False)
    host_option = models.BooleanField(default=False)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
    )

    def __str__(self):
        return 'Quiz({})'.format(self.name)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'quizzes'

    @staticmethod
    def get_self_quizzes():
        '''
        Retrieves all quizzes that can be self quizzed.
        '''
        return QuizModel.objects.filter(self_quiz_option=True)

    @staticmethod
    def get_hosted_quizzes(user: User):
        '''
        Retrieves all quizzes that can be hosted by the current user.
        '''
        if not user.is_authenticated:
            return []

        return QuizModel.objects.filter(
            host_option=True,
            owner=user
        )


class CategoryModel(models.Model):
    name = models.CharField(max_length=100)
    quiz = models.ForeignKey(
        QuizModel,
        on_delete=models.CASCADE,
        null=False,
        related_name='categories')

    def __str__(self):
        return '{} - {}'.format(self.quiz.name, self.name)

    class Meta:
        ordering = ['quiz', 'name']


class QuestionModel(models.Model):
    value = models.PositiveIntegerField()
    category = models.ForeignKey(
        CategoryModel,
        on_delete=models.CASCADE,
        null=False,
        related_name='questions'
    )
    question_text = models.TextField()
    solution_text = models.TextField()

    def __str__(self):
        return '{}: {}'.format(self.category, self.value)

    class Meta:
        ordering = ['category', 'value']

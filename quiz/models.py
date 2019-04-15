from django.db import models

class QuizModel(models.Model):
	name = models.CharField(max_length=100, unique=True, blank=False, null=False)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return 'Quiz({})'.format(self.name)

	class Meta:
		ordering = ['name']
		verbose_name_plural = 'quizzes'

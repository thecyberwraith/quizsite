import django.views.generic as generic

import itertools
import logging

from .models import QuizModel

class QuizSelectPage(generic.ListView):
	'''
	The homepage which allows a client to choose an available quiz to start.
	'''
	context_object_name = 'available_quizzes'
	queryset = QuizModel.objects.filter(is_active=True)
	template_name = 'quiz/selectquiz.html'


class QuizPage(generic.DetailView):
	model = QuizModel
	context_object_name = 'quiz'
	template_name = 'quiz/selectquestion.html'

	def get_context_data(self, **kwargs):
		context = super(QuizPage, self).get_context_data(**kwargs)
		quiz = context['quiz']

		categories = list(quiz.categories.all())
		uneven_questions = [list(c.questions.all()) for c in categories]
		evened_questions = tuple(itertools.zip_longest(*uneven_questions))
		context['categories'] = categories
		context['questions'] = evened_questions

		return context

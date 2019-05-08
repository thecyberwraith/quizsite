from django.shortcuts import redirect
import django.views.generic as generic
from django.urls import reverse

import itertools
import logging

from .models import QuizModel, QuestionModel

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


class QuestionPage(generic.DetailView):
	model = QuestionModel
	context_object_name = 'question'
	template_name = 'quiz/questiondetail.html'
	
	def get_context_data(self, **kwargs):
		context = super(QuestionPage, self).get_context_data(**kwargs)
		context['question_string'] = str(context['question'])
		return context


class QuizStartRedirect(generic.View):
	def get(self, request, pk):
		request.session['quiz'] = pk
		request.session['answered'] = []
		request.session['score'] = 0
		return redirect(reverse('quiz:quiz', kwargs={'pk': pk}))


class QuizAnswerQuestionRedirect(generic.View):
	def get(self, request, pk, correct):
		print(pk)
		question = QuestionModel.objects.get(pk=pk)
		if pk not in request.session['answered']:
			request.session['answered'].append(pk)
			if correct == 1:
				request.session['score'] += question.value
			request.session.modified=True
		print(request.session['answered'])
		return redirect(
			reverse('quiz:quiz', kwargs={'pk': question.category.quiz.id})
			)

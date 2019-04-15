from django.test import TestCase
from django.urls import reverse

from .models import QuizModel

class TestHomePage(TestCase):
	def get_response(self):
		return self.client.get(reverse('quiz:select'))

	def test_home_page_reachable(self):
		response = self.get_response()
		self.assertEqual(response.status_code, 200)
	
	def test_no_available_quizzes_message(self):
		response = self.get_response()
		self.assertContains(response, 'No quizzes are available.')
		self.assertEqual(list(response.context['available_quizzes']), [])

	def test_available_quizzes_message(self):
		q = QuizModel.objects.create(name='Sample Quiz')
		response = self.get_response()
		self.assertContains(response, 'Select an available quiz below.')
		self.assertEqual(list(response.context['available_quizzes']), [q,])
	
	def test_only_available_quizzes_shown(self):
		q = QuizModel.objects.create(name='Real Quiz')
		QuizModel.objects.create(name='Inactive Quiz', is_active=False)
		response = self.get_response()
		self.assertEqual(list(response.context['available_quizzes']), [q,])

class TestQuizModel(TestCase):
	def test_construction_of_regular_one(self):
		QuizModel(name='A Boring Quiz')
	
	def test_defaults_to_active(self):
		q = QuizModel(name='Who cares')
		self.assertTrue(q.is_active)
	
	def test_string_method(self):
		quiz = QuizModel(name='A Quiz')
		self.assertEqual(str(quiz), 'Quiz(A Quiz)')
	
	def test_default_sorting_is_on_name(self):
		b = QuizModel.objects.create(name='Not the first')
		a = QuizModel.objects.create(name='Am first')
		ordered = list(QuizModel.objects.all())
		self.assertEqual(ordered, [a,b])

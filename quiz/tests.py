from django.test import TestCase
from django.urls import reverse

from .models import QuizModel, CategoryModel, QuestionModel

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

	def test_available_quiz_table_row(self):
		q = QuizModel.objects.create(name='A Quiz')
		response = self.get_response()
		self.assertContains(response, 'A Quiz')


class TestQuizModel(TestCase):
	def test_construction_of_regular_one(self):
		QuizModel.objects.create(name='A Boring Quiz')

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


class TestCategoryModel(TestCase):
	def setUp(self):
		self.a_quiz = QuizModel.objects.create(name='A Quiz')

	def test_construction_of_regular_object(self):
		CategoryModel.objects.create(name='A Category', quiz=self.a_quiz)

	def test_quiz_requirement(self):
		with self.assertRaises(Exception):
			CategoryModel.objects.create(name='A Category')

	def test_str_method(self):
		category = CategoryModel(name='A Category', quiz=self.a_quiz)
		self.assertEqual(str(category), 'A Quiz - A Category')

	def test_cascading_delete(self):
		category = CategoryModel.objects.create(
			name = 'A Category',
			quiz = self.a_quiz
		)
		categories = CategoryModel.objects.all()
		self.assertEqual(len(categories), 1)
		self.a_quiz.delete()
		categories = CategoryModel.objects.all()
		self.assertEqual(len(categories), 0)

	def test_category_ordering(self):
		quiz = QuizModel.objects.create(name='1 Quiz')
		a = CategoryModel.objects.create(name='a', quiz=self.a_quiz)
		b = CategoryModel.objects.create(name='2', quiz=self.a_quiz)
		c = CategoryModel.objects.create(name='1', quiz=quiz)
		d = CategoryModel.objects.create(name='b', quiz=quiz)
		categories = list(CategoryModel.objects.all())
		self.assertEqual(categories, [c,d,b,a])


class TestQuestionModel(TestCase):
	def setUp(self):
		self.quiz = QuizModel.objects.create(name='A Quiz')
		self.category = CategoryModel.objects.create(
				name = 'A Category',
				quiz = self.quiz
		)

	def make_question(self):
		self.question = QuestionModel.objects.create(
			value = 100,
			category = self.category,
			question_text = 'Who are you?',
			solution_text = 'Nobody.'
		)
	def test_construction_of_regular_object(self):
		self.make_question()

	def test_quiz_cascading_delete(self):
		self.make_question()
		self.assertEqual(len(QuestionModel.objects.all()), 1)
		self.quiz.delete()
		self.assertEqual(len(QuestionModel.objects.all()), 0)

	def test_category_cascading_delete(self):
		self.make_question()
		self.assertEqual(len(QuestionModel.objects.all()), 1)
		self.category.delete()
		self.assertEqual(len(QuestionModel.objects.all()), 0)

	def test_str_method(self):
		self.make_question()
		self.assertEqual(str(self.question), 'A Quiz - A Category: 100')

	def test_sort_order(self):
		self.make_question()
		cb = CategoryModel.objects.create(name='CB', quiz=self.quiz)
		qb = QuestionModel.objects.create(value=50, category=cb)
		qc = QuestionModel.objects.create(value=101, category=self.category)
		questions = list(QuestionModel.objects.all())
		self.assertEqual(questions, [self.question, qc, qb])

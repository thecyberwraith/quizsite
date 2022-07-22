from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import QuizModel, CategoryModel, QuestionModel
from livequiz.models import LiveQuizModel, QuizData

class TestLaunchLiveQuizRedirect(TestCase):
    FAIL_URL = reverse('quiz:select')

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            username='launch',
            password='away'
        )
        cls.quiz = QuizModel.objects.create(name='Test Quiz', owner=cls.user)
        cat = cls.quiz.categories.create(name='A')
        cat.questions.create(value=100, question_text='Qho', solution_text='Tho')

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def get_response(self, quiz_id=1):
        return self.client.post(
            reverse('quiz:launchlive'),
            data={'quiz_id': quiz_id},
            follow=True
        )

    def test_redirects_to_list_if_not_logged_in(self):
        self.client.logout()

        response = self.get_response()

        self.assertRedirects(
            response,
            self.FAIL_URL
        )

    def test_redirects_to_list_if_quiz_does_not_exist(self):
        response = self.get_response(self.quiz.id+1)

        self.assertRedirects(
            response,
            self.FAIL_URL
        )

    def test_redirects_to_list_if_quiz_is_not_owned(self):
        self.quiz.owner = None
        self.quiz.save()
        response = self.get_response(self.quiz.id)

        self.assertRedirects(
            response,
            self.FAIL_URL
        )

    def test_redirects_and_live_quiz_created_if_owned(self):
        self.assertEqual(LiveQuizModel.objects.all().count(), 0)
        response = self.get_response(self.quiz.id)

        self.assertEqual(LiveQuizModel.objects.all().count(), 1)

        livequiz = LiveQuizModel.objects.all().first()

        self.assertRedirects(
            response,
            reverse('livequiz:host', kwargs={'quiz_code': livequiz.code})
        )



class TestHostableQuizList(TestCase):
    HOST_SECTION_TEXT = 'Start Live Quiz'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='bob', password='nob')

    def setUp(self):
        self.client.force_login(self.user)

    def get_response(self):
        return self.client.get(reverse('quiz:select'))

    def test_no_hosted_quizzes_shown_if_not_owned(self):
        a = User.objects.create_user(username='sue', password='what')
        QuizModel.objects.create(
            name='Not my quiz.',
            host_option=True,
            owner=a
        )

        response = self.get_response()

        self.assertNotContains(response, self.HOST_SECTION_TEXT)
        self.assertListEqual(list(response.context['host_quizzes']), [])

    def test_hosted_quiz_shown_if_owned(self):
        quiz = QuizModel.objects.create(
            name='Host me baby.',
            host_option=True,
            owner=self.user
        )
        response = self.get_response()
        self.assertListEqual(list(response.context['host_quizzes']), [quiz])
        self.assertContains(response, self.HOST_SECTION_TEXT)
        self.assertContains(response, quiz.name)



class TestSelfQuizListPage(TestCase):
    def get_response(self):
        return self.client.get(reverse('quiz:select'))

    def test_home_page_reachable(self):
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_no_available_self_quizzes_message(self):
        response = self.get_response()
        self.assertContains(response, 'No quizzes are available.')
        self.assertEqual(list(response.context['self_quizzes']), [])

    def test_available_quizzes_display(self):
        q = QuizModel.objects.create(name='Sample Quiz', self_quiz_option=True)
        response = self.get_response()
        self.assertContains(response, 'Select an available quiz below.')
        self.assertEqual(list(response.context['self_quizzes']), [q, ])
        self.assertContains(response, q.name)


class TestAnswerQuestionPage(TestCase):
    def setUp(self):
        quiz = QuizModel.objects.create(name='A quiz')
        category = CategoryModel.objects.create(name='A Cat', quiz=quiz)
        self.question = QuestionModel.objects.create(
            category=category,
            question_text='Q',
            solution_text='A',
            value=143
        )
        self.client.get(
            reverse('quiz:start', kwargs={'pk': quiz.id})
        )

    def get_response(self, correct=0, follow=False):
        return self.client.get(
            reverse(
                'quiz:answer',
                kwargs={'pk': self.question.id, 'correct': correct},
            ),
            follow=follow,
        )

    def test_redirect_to_quiz_page(self):
        response = self.get_response()
        self.assertRedirects(
            response,
            reverse('quiz:quiz', kwargs={
                    'pk': self.question.category.quiz.id}),
            status_code=302,
            target_status_code=200,
        )

    def test_correct_answer(self):
        self.get_response(
            correct=1,
            follow=True
        )
        self.assertEqual(self.client.session.get('score'), self.question.value)
        self.assertIn(self.question.id, self.client.session.get('answered'))

    def test_incorrect_answer(self):
        self.get_response(
            correct=0,
            follow=True
        )
        self.assertEqual(self.client.session.get('score'), 0)
        self.assertIn(self.question.id, self.client.session.get('answered'))

    def test_no_doubling(self):
        self.get_response(correct=1, follow=True)
        self.get_response(correct=1, follow=True)
        self.assertEqual(self.client.session.get('score'), self.question.value)
        self.assertEqual(self.client.session.get(
            'answered'), [self.question.id])


class TestStartPage(TestCase):
    def setUp(self):
        self.quiz = QuizModel.objects.create(name='A Quiz')
        self.response = self.client.get(
            reverse('quiz:start', kwargs={'pk': self.quiz.id}))

    def test_redirection_status(self):
        self.assertRedirects(
            self.response,
            reverse('quiz:quiz', kwargs={'pk': self.quiz.id}),
            status_code=302,
            target_status_code=200,
        )

    def test_session_initialization(self):
        self.assertEqual(self.client.session['quiz'], self.quiz.id)
        self.assertEqual(self.client.session['answered'], [])
        self.assertEqual(self.client.session['score'], 0)


class TestQuizPage(TestCase):
    def setUp(self):
        self.quiz = QuizModel.objects.create(name='A Quiz')
        self.catA = CategoryModel.objects.create(
            name='First Cat',
            quiz=self.quiz,
        )
        self.catB = CategoryModel.objects.create(
            name='Actually First',
            quiz=self.quiz,
        )
        self.questA1 = QuestionModel.objects.create(
            value=100,
            question_text='A question',
            solution_text='A solution',
            category=self.catA,
        )
        self.questA2 = QuestionModel.objects.create(
            value=200,
            question_text='An question',
            solution_text='A solution',
            category=self.catA,
        )
        self.questB1 = QuestionModel.objects.create(
            value=150,
            question_text='B question',
            solution_text='B solution',
            category=self.catB,
        )
        self.response = self.client.get(
            reverse(
                'quiz:start',
                kwargs={'pk': self.quiz.id}
            ),
            follow=True
        )

    def test_page_reachable(self):
        self.assertEqual(self.response.status_code, 200)

    def test_page_has_quiz_context(self):
        self.assertEqual(self.response.context['quiz'], self.quiz)

    def test_page_has_categories(self):
        self.assertEqual(
            list(self.response.context['categories']),
            [self.catB, self.catA]
        )

    def test_page_has_uneven_question_lists(self):
        self.assertEqual(
            self.response.context['questions'],
            (
                        (self.questB1, self.questA1),
                        (None, self.questA2)
            )
        )

    def test_category_names_appear(self):
        self.assertContains(
            self.response,
            'First Cat'
        )
        self.assertContains(
            self.response,
            'Actually First'
        )

    def test_values_appear(self):
        for value in [100, 150, 200]:
            self.assertContains(
                self.response,
                str(value)
            )


class TestQuestionPage(TestCase):
    def setUp(self):
        self.quiz = QuizModel.objects.create(name='A Quiz')
        self.category = CategoryModel.objects.create(
            name='Category',
            quiz=self.quiz,
        )
        self.question = QuestionModel.objects.create(
            value=100,
            question_text='Here is a question',
            solution_text='Here is my solution',
            category=self.category,
        )
        self.client.get(
            reverse(
                'quiz:start',
                kwargs={'pk': self.quiz.id}
            )
        )
        self.response = self.client.get(
            reverse(
                'quiz:question',
                kwargs={'pk': self.question.id},
            )
        )

    def test_200_result(self):
        self.assertEqual(self.response.status_code, 200)

    def test_page_has_text(self):
        text_samples = [
            'Here is a question',
            'Here is my solution',
            str(self.question),  # In the title
        ]
        for text in text_samples:
            self.assertContains(self.response, text)


class TestQuizModel(TestCase):
    def test_construction_of_regular_one(self):
        QuizModel.objects.create(name='A Boring Quiz')

    def test_defaults_to_not_available(self):
        q = QuizModel(name='Who cares')
        self.assertFalse(q.host_option)
        self.assertFalse(q.self_quiz_option)

    def test_string_method(self):
        quiz = QuizModel(name='A Quiz')
        self.assertEqual(str(quiz), 'Quiz(A Quiz)')

    def test_default_sorting_is_on_name(self):
        b = QuizModel.objects.create(name='Not the first')
        a = QuizModel.objects.create(name='Am first')
        ordered = list(QuizModel.objects.all())
        self.assertEqual(ordered, [a, b])


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
            name='A Category',
            quiz=self.a_quiz
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
        self.assertEqual(categories, [c, d, b, a])


class TestQuestionModel(TestCase):
    def setUp(self):
        self.quiz = QuizModel.objects.create(name='A Quiz')
        self.category = CategoryModel.objects.create(
            name='A Category',
            quiz=self.quiz
        )

    def make_question(self):
        self.question = QuestionModel.objects.create(
            value=100,
            category=self.category,
            question_text='Who are you?',
            solution_text='Nobody.'
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

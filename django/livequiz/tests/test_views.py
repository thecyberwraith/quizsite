from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from quiz.models import QuizModel
from livequiz.models import LiveQuizModel


class TestHostableQuizList(TestCase):
    HOST_SECTION_TEXT = 'Host a quiz below.'
    NO_QUIZZES_FOUND_TEXT = 'No quizzes are available to host.'

    def setUp(self):
        self.user = User.objects.create_user(username='bob', password='nob')
        self.client.login(username='bob', password='nob')

    def get_response(self):
        return self.client.get(reverse('livequiz:list'))

    def test_no_hosted_quizzes_section_shown_if_not_logged_in(self):
        self.client.logout()
        QuizModel.objects.create(name='A hosting quiz', host_option=True)
        self.assertNotContains(self.get_response(), self.HOST_SECTION_TEXT)

    def test_hosted_quizzes_section_shown_if_logged_in(self):
        self.assertContains(self.get_response(), self.HOST_SECTION_TEXT)

    def test_no_hosted_quizzes_shown_if_not_owned(self):
        a = User.objects.create_user(username='sue', password='what')
        q = QuizModel.objects.create(
            name='Not my quiz.',
            host_option=True,
            owner=a
        )

        response = self.get_response()

        self.assertContains(response, self.NO_QUIZZES_FOUND_TEXT)
        self.assertListEqual(list(response.context['host_quizzes']), [])

    def test_hosted_quiz_shown_if_owned(self):
        quiz = QuizModel.objects.create(
            name='Host me baby.',
            host_option=True,
            owner=self.user
        )
        response = self.get_response()
        self.assertContains(response, 'Host a quiz below.')
        self.assertContains(response, quiz.name)
        self.assertListEqual(list(response.context['host_quizzes']), [quiz])


class LaunchPageTest(TestCase):
    FAIL_URL = reverse('livequiz:list')

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='launch', password='away')
        self.client.login(username='launch', password='away')
        self.quiz = QuizModel.objects.create(name='A Quiz', owner=self.user)

    def get_response(self, quiz_id=1):
        return self.client.get(
            reverse('livequiz:launch', kwargs={'quiz_id': quiz_id}),
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


class PageBasedTest(TestCase):
    '''A test that gets a page referenced by a reverse tag.'''
    page_url_key = 'nope'
    page_kwargs = None

    def get_response(self):
        '''Perform a get request referenced by 'page_url_key and return the response.'''
        return self.client.get(reverse(self.page_url_key, kwargs=self.page_kwargs))


class TestJoinPage(PageBasedTest):
    page_url_key = 'livequiz:join'

    def test_reachable(self):
        self.assertEqual(self.get_response().status_code, 200)


class TestPlayPage(PageBasedTest):
    page_url_key = 'livequiz:play'
    page_kwargs = {'quiz_code': 'abcde'}

    def test_reachable(self):
        self.assertEqual(self.get_response().status_code, 200)


class TestHostPage(PageBasedTest):
    page_url_key = 'livequiz:host'
    page_kwargs = {'quiz_code': 'abcde'}

    def test_reachable(self):
        self.assertEqual(self.get_response().status_code, 200)

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from quiz.models import QuizModel


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


class PageBasedTest(TestCase):
    '''A test that gets a page referenced by a reverse tag.'''
    page_url_key = 'nope'
    page_kwargs = None

    def get_response(self):
        '''Perform a get request referenced by 'page_url_key and return the response.'''
        return self.client.get(reverse(self.page_url_key, kwargs=self.page_kwargs))


class LaunchPageTest(TestCase):
    def get_response(self, code=1):
        return self.client.get(
            reverse('livequiz:launch'),
            kwargs={'quiz_id': id},
            follow=True
        )

    # def test_redirects_to_join_if_not_logged_in(self):
    #     response = self.get_response()
    #     self.assertRedirects(
    #         self.get_response(),
    #         reverse(TestJoinPage.page_url_key)
    #     )

    # def test_redirects_to_join_if_quiz_does_not_exist(self):


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

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from livequiz.models import LiveQuizModel, QuizData


class TestLiveQuizList(TestCase):
    LIVE_QUIZ_LIST_TEXT = 'Active Live Quizzes'
    LIVE_QUIZ_NO_QUIZZES_TEXT = 'There are no live quizzes.'

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(username='bob', password='test')

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def get_response(self):
        return self.client.get(reverse('livequiz:list'))

    def test_no_live_quizzes_shown_if_not_logged_in(self):
        self.client.logout()

        self.assertNotContains(
            self.get_response(),
            self.LIVE_QUIZ_LIST_TEXT
        )

    def test_empty_live_quizzes_show_if_logged_in_with_no_quizzes(self):
        response = self.get_response()

        self.assertContains(
            response,
            self.LIVE_QUIZ_NO_QUIZZES_TEXT
        )
        self.assertContains(
            response,
            self.LIVE_QUIZ_LIST_TEXT
        )

    def test_empty_live_quizzes_shown_if_logged_in_and_not_owned(self):
        other_user = User.objects.create_user(username='sue', password='sue')
        LiveQuizModel.objects.create_for_quiz(other_user, QuizData(name='Test', categories={}))

        response = self.get_response()

        self.assertContains(
            response,
            self.LIVE_QUIZ_NO_QUIZZES_TEXT
        )
        self.assertNotContains(
            response,
            'Other Quiz'
        )

    def test_live_quiz_shown_if_logged_in_and_owned(self):
        LiveQuizModel.objects.create_for_quiz(self.user, QuizData(name='Test', categories={}))

        response = self.get_response()

        self.assertContains(
            response,
            'Test'
        )
        self.assertContains(
            response,
            self.LIVE_QUIZ_LIST_TEXT
        )
        self.assertNotContains(
            response,
            self.LIVE_QUIZ_NO_QUIZZES_TEXT
        )


class TestDeletePage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='linda', password='belcher')
        cls.livequiz = LiveQuizModel.objects.create_for_quiz(
            cls.user,
            QuizData(name='something', categories={})
        )

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def get_response(self, livequiz_code=None):
        if livequiz_code is None:
            livequiz_code = self.livequiz.code

        return self.client.post(
            reverse('livequiz:delete'),
            data={'livequiz_code': livequiz_code},
            follow=True
        )

    def test_does_nothing_if_quiz_is_not_owned_by_user(self):
        livequiz = LiveQuizModel.objects.create_for_quiz(
            User.objects.create_user(username='sue', password='falls'),
            QuizData(name='Dummy', categories={})
        )

        self.assertEqual(LiveQuizModel.objects.filter(
            code=livequiz.code).count(), 1)

        response = self.get_response(livequiz.code)

        self.assertEqual(LiveQuizModel.objects.filter(
            code=livequiz.code).count(), 1)
        self.assertRedirects(
            response,
            reverse('livequiz:list')
        )

    def test_does_nothing_if_quiz_does_not_exist(self):
        response = self.get_response(self.livequiz.code + 'X')
        self.assertRedirects(
            response,
            reverse('livequiz:list')
        )

    def test_delete_quiz_if_owned(self):
        response = self.get_response()
        self.assertRedirects(
            response,
            reverse('livequiz:list')
        )
        self.assertEqual(LiveQuizModel.objects.filter(
            code=self.livequiz.code).count(), 0)


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

    def test_websocket_url(self):
        self.assertContains(
            self.get_response(),
            "setup('abcde')"
        )

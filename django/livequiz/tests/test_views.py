from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from quiz.models import QuizModel
from livequiz.models import LiveQuizModel


class TestHostableQuizList(TestCase):
    HOST_SECTION_TEXT = 'Host a quiz below.'
    NO_QUIZZES_FOUND_TEXT = 'No quizzes are available to host.'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='bob', password='nob')

    def setUp(self):
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


class TestLiveQuizList(TestCase):
    LIVE_QUIZ_LIST_TEXT = 'Active Live Quizzes'
    LIVE_QUIZ_NO_QUIZZES_TEXT = 'There are no live quizzes.'

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(username='bob', password='test')
        cls.quiz = QuizModel.objects.create(
            name='A quiz',
            owner=cls.user)

    def setUp(self) -> None:
        self.client.login(username='bob', password='test')

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
        other_quiz = QuizModel.objects.create(
            name='Other Quiz', owner=other_user)
        LiveQuizModel.objects.create_for_quiz(other_quiz.id)

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
        LiveQuizModel.objects.create_for_quiz(self.quiz.id)

        response = self.get_response()

        self.assertContains(
            response,
            self.quiz.name
        )
        self.assertContains(
            response,
            self.LIVE_QUIZ_LIST_TEXT
        )
        self.assertNotContains(
            response,
            self.LIVE_QUIZ_NO_QUIZZES_TEXT
        )


class TestLaunchPage(TestCase):
    FAIL_URL = reverse('livequiz:list')

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            username='launch',
            password='away'
        )
        cls.quiz = QuizModel.objects.create(name='A Quiz', owner=cls.user)

    def setUp(self) -> None:
        self.client.login(username='launch', password='away')

    def get_response(self, quiz_id=1):
        return self.client.post(
            reverse('livequiz:launch'),
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


class TestDeletePage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='linda', password='belcher')
        cls.quiz = QuizModel.objects.create(name='something', owner=cls.user)
        cls.livequiz = LiveQuizModel.objects.create_for_quiz(cls.quiz.id)

    def setUp(self) -> None:
        self.client.login(username='linda', password='belcher')

    def get_response(self, livequiz_code=None):
        if livequiz_code is None:
            livequiz_code = self.livequiz.code

        return self.client.post(
            reverse('livequiz:delete'),
            data={'livequiz_code': livequiz_code},
            follow=True
        )

    def test_does_nothing_if_quiz_is_not_owned_by_user(self):
        other_quiz = QuizModel.objects.create(name='Dummy')
        livequiz = LiveQuizModel.objects.create_for_quiz(other_quiz.id)

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

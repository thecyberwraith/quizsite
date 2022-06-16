from django.test import TestCase
from django.urls import reverse


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

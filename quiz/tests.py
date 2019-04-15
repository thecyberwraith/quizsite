from django.test import TestCase
from django.urls import reverse

class TestHomePage(TestCase):
	def test_home_page_reachable(self):
		'''
		Simply try to get the home page to render without errors.
		'''
		response = self.client.get(reverse('quiz:index'))
		self.assertEqual(response.status_code, 200)

from django.views.generic import ListView
from .models import QuizModel

class QuizSelectPage(ListView):
	'''
	The homepage which allows a client to choose an available quiz to start.
	'''
	context_object_name = 'available_quizzes'
	queryset = QuizModel.objects.filter(is_active=True)
	template_name = 'quiz/selectquiz.html'

from django.shortcuts import render

# Create your views here.

def index(request):
	'''
	The homepage, which lists the available quizzes.
	'''
	context = dict()
	return render(request, 'quiz/index.html', context)

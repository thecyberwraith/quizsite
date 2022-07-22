from django.urls import path

from . import views

app_name = 'quiz'

urlpatterns = [
	path('', views.QuizSelectPage.as_view(), name='select'),
	path('launch/live/', views.LaunchLiveQuizRedirect.as_view(), name='launchlive'),
	path('quiz/<int:pk>/', views.QuizPage.as_view(), name='quiz'),
	path('question/<int:pk>/', views.QuestionPage.as_view(), name='question'),
	path('start/<int:pk>', views.QuizStartRedirect.as_view(), name='start'),
	path('answer/<int:pk>/<int:correct>', views.QuizAnswerQuestionRedirect.as_view(), name='answer'),
]

import re
from typing import Any
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView, View

from livequiz.models import LiveQuizModel
from quiz.models import QuizModel


class ListHostableQuizzesPage(TemplateView):
    template_name = 'livequiz/list_hostable.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['host_quizzes'] = QuizModel.get_hosted_quizzes(self.request.user)
        context['live_quizzes'] = LiveQuizModel.objects.owned_by_user(self.request.user)
        return context

class LaunchRedirect(View):
    '''Performed setup for an authenticated user to launch a game.'''

    def post(self, request):
        quiz_id = request.POST['quiz_id']
        fail_redirect = redirect(reverse('livequiz:list'))

        if not request.user.is_authenticated:
            return fail_redirect

        try:
            quiz = QuizModel.objects.get(id=quiz_id)
        except QuizModel.DoesNotExist:
            return fail_redirect

        if quiz.owner != request.user:
            return fail_redirect

        livequiz = LiveQuizModel.objects.create_for_quiz(quiz_id)

        return redirect(reverse('livequiz:host', kwargs={'quiz_code': livequiz.code}))


class DeleteRedirect(View):
    '''Remove a particular live quiz.'''

    def post(self, request):
        return_value = redirect(reverse('livequiz:list'))
        livequiz_code = request.POST['livequiz_code']
        if not request.user.is_authenticated:
            return return_value
        
        try:
            livequiz = LiveQuizModel.objects.get(code=livequiz_code)
            if livequiz.quiz.owner == request.user:
                livequiz.delete()
        except LiveQuizModel.DoesNotExist:
            pass
    
        return return_value


class JoinPage(TemplateView):
    '''A page for a user to join a game as a participant.'''
    template_name = 'livequiz/join.html'


class FixedQuizPage(TemplateView):
    '''A page that references a specific active quiz.'''

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["quiz_code"] = kwargs['quiz_code']
        return context

class HostPage(FixedQuizPage):
    '''The view that the host gets of a live quiz.'''
    template_name = 'livequiz/host.html'


class PlayPage(FixedQuizPage):
    '''The view that the participants get of a live quiz.'''
    template_name = 'livequiz/participate.html'

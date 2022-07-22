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
        context['host_quizzes'] = QuizModel.get_hosted_quizzes(
            self.request.user)
        context['live_quizzes'] = LiveQuizModel.objects.owned_by_user(
            self.request.user)
        return context


class DeleteRedirect(View):
    '''Remove a particular live quiz.'''

    def post(self, request):
        return_value = redirect(reverse('livequiz:list'))
        livequiz_code = request.POST['livequiz_code']
        if not request.user.is_authenticated:
            return return_value

        try:
            live_quiz = LiveQuizModel.objects.get(code=livequiz_code)
            if live_quiz.host == request.user:
                live_quiz.delete()
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

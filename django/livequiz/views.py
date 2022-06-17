from typing import Any
from django.views.generic import ListView, TemplateView, View

from quiz.models import QuizModel


class ListHostableQuizzesPage(ListView):
    template_name = 'livequiz/list_hostable.html'
    context_object_name = 'host_quizzes'

    def get_queryset(self):
        return QuizModel.get_hosted_quizzes(self.request.user)


class LaunchRedirect(View):
    '''Performed setup for an authenticated user to launch a game.'''

    def get(self, request, quiz_code):
        return


class JoinPage(TemplateView):
    '''A page for a user to join a game as a participant.'''
    template_name = 'livequiz/join.html'


class FixedQuizPage(TemplateView):
    '''A page that references a specific active quiz.'''

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["quiz_code"] = kwargs['quiz_code']


class HostPage(FixedQuizPage):
    '''The view that the host gets of a live quiz.'''
    template_name = 'livequiz/host.html'


class PlayPage(FixedQuizPage):
    '''The view that the participants get of a live quiz.'''
    template_name = 'livequiz/participate.html'

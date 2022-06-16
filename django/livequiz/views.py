from typing import Any
from django.views.generic import TemplateView, View


class JoinPage(TemplateView):
    '''A page for a user to join a game as a participant.'''
    template_name = 'livequiz/join.html'


class FixedQuizPage(TemplateView):
    '''A page that references a specific active quiz.'''

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["quiz_code"] = kwargs['quiz_code']


class LaunchRedirect(View):
    '''Performed setup for an authenticated user to launch a game.'''


class HostPage(FixedQuizPage):
    '''The view that the host gets of a live quiz.'''
    template_name = 'livequiz/host.html'


class PlayPage(FixedQuizPage):
    '''The view that the participants get of a live quiz.'''
    template_name = 'livequiz/participate.html'

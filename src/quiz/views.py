from typing import Any
import itertools

from django.shortcuts import redirect
import django.views.generic as generic
from django.urls import reverse

from .models import QuizModel, QuestionModel
from livequiz.models import LiveQuizModel, QuizData


class QuizSelectPage(generic.TemplateView):
    '''
    The homepage which allows a client to choose an available quiz to start.
    '''
    template_name = 'quiz/selectquiz.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context['self_quizzes'] = list(QuizModel.get_self_quizzes())
        context['host_quizzes'] = list(QuizModel.get_hosted_quizzes(self.request.user))
        context['available_quizzes'] = sorted(set(context['self_quizzes'] + context['host_quizzes']))

        return context


class QuizPage(generic.DetailView):
    model = QuizModel
    context_object_name = 'quiz'
    template_name = 'quiz/selectquestion.html'

    def get_context_data(self, **kwargs):
        context = super(QuizPage, self).get_context_data(**kwargs)
        quiz = context['quiz']

        categories = list(quiz.categories.all())
        uneven_questions = [list(c.questions.all()) for c in categories]
        evened_questions = tuple(itertools.zip_longest(*uneven_questions))
        context['categories'] = categories
        context['questions'] = evened_questions

        return context


class QuestionPage(generic.DetailView):
    model = QuestionModel
    context_object_name = 'question'
    template_name = 'quiz/questiondetail.html'

    def get_context_data(self, **kwargs):
        context = super(QuestionPage, self).get_context_data(**kwargs)
        context['question_string'] = str(context['question'])
        return context


class QuizStartRedirect(generic.View):
    def get(self, request, pk):
        request.session['quiz'] = pk
        request.session['answered'] = []
        request.session['score'] = 0
        return redirect(reverse('quiz:quiz', kwargs={'pk': pk}))


class QuizAnswerQuestionRedirect(generic.View):
    def get(self, request, pk, correct):
        question = QuestionModel.objects.get(pk=pk)
        if pk not in request.session['answered']:
            request.session['answered'].append(pk)
            if correct == 1:
                request.session['score'] += question.value
            request.session.modified = True
        return redirect(
            reverse('quiz:quiz', kwargs={'pk': question.category.quiz.id})
        )


class LaunchLiveQuizRedirect(generic.View):
    '''Performed setup for an authenticated user to launch a game.'''

    def post(self, request):
        quiz_id = request.POST['quiz_id']
        fail_redirect = redirect(reverse('quiz:select'))

        if not request.user.is_authenticated:
            return fail_redirect

        try:
            quiz = QuizModel.objects.get(id=quiz_id)
        except QuizModel.DoesNotExist:
            return fail_redirect

        if quiz.owner != request.user:
            return fail_redirect

        livequiz = LiveQuizModel.objects.create_for_quiz(
            quiz.owner, to_livequiz_data(quiz))

        return redirect(reverse('livequiz:host', kwargs={'quiz_code': livequiz.code}))


def to_livequiz_data(quiz: QuizModel) -> QuizData:
    '''Converts a quiz to the data structure for a live quiz.'''
    return QuizData(
        name=quiz.name,
        categories={cat.name: [(q.value, q.question_text, q.solution_text)
                               for q in cat.questions.all()] for cat in quiz.categories.all()}
    )

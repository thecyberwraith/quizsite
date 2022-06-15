from typing import Any
import itertools

from django.shortcuts import redirect
import django.views.generic as generic
from django.urls import reverse

from .models import QuizModel, QuestionModel


class QuizSelectPage(generic.TemplateView):
    '''
    The homepage which allows a client to choose an available quiz to start.
    '''
    template_name = 'quiz/selectquiz.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        quizzes = []

        if self.request.user.is_authenticated:
            quizzes = QuizModel.get_hosted_quizzes(self.request.user)
        context['host_quizzes'] = quizzes

        context['self_quizzes'] = QuizModel.get_self_quizzes()

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

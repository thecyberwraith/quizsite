from django.contrib import admin

from . import models

admin.site.register(models.QuizModel)
admin.site.register(models.CategoryModel)
admin.site.register(models.QuestionModel)

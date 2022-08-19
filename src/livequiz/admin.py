from django.contrib import admin
from livequiz.models import LiveQuizModel, LiveQuizParticipant

admin.site.register(LiveQuizModel)
admin.site.register(LiveQuizParticipant)
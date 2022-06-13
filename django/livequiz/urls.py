from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='join', permanent=False), name='join'),
    path('join/', views.join, name='join'),
    path('play/<str:game_code>/', views.play, name='play'),
]
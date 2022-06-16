from django.urls import path
from django.views.generic.base import RedirectView

from . import views

app_name = 'livequiz'

urlpatterns = [
    path('', RedirectView.as_view(url='join', permanent=False)),
    path('join/', views.JoinPage.as_view(), name='join'),
    path('launch/<int:quiz_id>', views.LaunchRedirect.as_view(), name='launch'),
    path('host/<str:quiz_code>', views.HostPage.as_view(), name='host'),
    path('play/<str:quiz_code>', views.PlayPage.as_view(), name='play'),
]
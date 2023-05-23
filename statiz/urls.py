from django.urls import re_path
from .views import *

urlpatterns = [
   re_path(r'^$', home, name='home'),
   re_path(r'^get', getDataAsync, name='getDataAsync'),
   re_path(r'^players', players, name='players'),
   re_path(r'^teams', teams, name='teams'),
]

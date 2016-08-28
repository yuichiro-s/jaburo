from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.search, name='search'),
    url(r'^lm$', views.lm, name='lm'),
    url(r'^search_phrases$', views.search_phrases, name='search_phrases'),
    url(r'^search_examples$', views.search_examples, name='search_examples'),
    url(r'^analyze$', views.analyze, name='analyze'),
    url(r'^generate$', views.generate, name='generate'),
]

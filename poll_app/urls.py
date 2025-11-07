from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_constituencies/<int:district_id>/', views.get_constituencies, name='get_constituencies'),
    path('filter-candidates/', views.filter_candidates, name='filter_candidates'),
    path("send-otp/", views.send_otp, name="send-otp"),

    path('verify-vote/', views.verify_vote, name='verify_vote'),
    path('submit-vote/', views.submit_vote, name='submit_vote'),

    path('news/', views.news, name='news'),
    path('<int:news_id>/', views.news_detail, name='news_detail'),
    path('overview', views.overview, name='overview'),

    path('blogs', views.blogs, name='blogs'),
]

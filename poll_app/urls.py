from django.urls import path, re_path

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
    path("login/", views.login_view, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("candidates/", views.Candidates, name="candidates"),
    path('get-constituencies/<int:district_id>/', views.get_constituencies, name='get_constituencies'),
    path('opinions/', views.opinion, name='opinion'),
    path('opinions/delete-selected/', views.delete_selected_opinions, name='delete_selected_opinions'),
    path('opinions/delete/<int:id>/', views.delete_opinion, name='delete_opinion'),
    path('admin_news/', views.admin_news, name='admin_news'),
    path('delete_news/<int:id>/', views.delete_news, name='delete_news'),
    path("delete-selected-news/", views.delete_selected_news, name="delete_selected_news"),
    path('admin_blog/', views.admin_blog, name='admin_blog'),
    path('add_category/', views.add_category, name='add_category'),
    path('delete_blog/<int:id>/', views.delete_blog, name='delete_blog'),
    path('admin_contact/', views.admin_contact, name='admin_contact'),
    path('delete_contact/<int:contact_id>/', views.delete_contact, name='delete_contact'),
    path('admin_party/', views.admin_party, name='admin_party'),
    path('add_party/', views.add_party, name='add_party'),
    path('delete-party/<int:party_id>/', views.delete_party, name='delete_party'),

    path('add_aligned_party/', views.add_aligned_party, name='add_aligned_party'),
    path('delete_aligned_party/<int:aligned_id>/', views.delete_aligned_party, name='delete_aligned_party'),

    path("vote", views.admin_votes, name="vote_analysis"),


    path("logout/", views.logout_view, name="logout"),

    re_path(r'^$', views.index, name='index'),


]

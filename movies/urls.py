from django.urls import path

from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_movie, name='create'),
    path('<int:pk>/', views.details, name='details'),
    path('<int:pk>/edit/', views.edit_movie, name='edit'),
    path('<int:pk>/delete/', views.delete_movie, name='delete'),
    path('<int:pk>/vote/', views.vote, name='vote'),
    path('users/', views.users_index, name='users_index'),
    path('users/<int:user_id>/toggle-admin/', views.toggle_admin, name='toggle_admin'),
    path('users/<int:user_id>/manage/', views.manage_user, name='manage_user'),
    path('visitors-book/', views.visitors_book, name='visitors_book'),
]

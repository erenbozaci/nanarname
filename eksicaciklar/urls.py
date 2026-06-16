"""
URL configuration for eksicaciklar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView
from movies import forms as movie_forms
from movies import views as movie_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='movies:index', permanent=False)),
    path('movies/', include('movies.urls')),
    path('accounts/register/', movie_views.register, name='register'),
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(authentication_form=movie_forms.CustomLoginForm),
        name='login',
    ),
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/kotusoz/', movie_views.check_bad_words, name='check_bad_words'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

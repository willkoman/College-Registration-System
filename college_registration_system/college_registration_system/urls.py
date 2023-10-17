"""
URL configuration for college_registration_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from registration import views

# urlpatterns = [
#     
    
# ]


urlpatterns = [
    # path('login/', views.login_view, name='login'),
    path('', views.root_redirect, name='root_redirect'),
    path('login/', views.user_login, name='user_login'),
    path('admin/login/', views.user_login, name='user_login'),
    path('admin/logout/', views.logout_view, name='logout'),
    path('homepage/', views.homepage, name='homepage'),
    path('logout/', views.logout_view, name='logout'),
    path('admin/', admin.site.urls),
    path('schedule/', views.schedule_view, name='schedule_view'),
]

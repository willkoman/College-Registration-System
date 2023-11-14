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
    path('admin_panel/', admin.site.urls),
    path('admin/', views.admin_view, name='admin_view'),
    path('schedule/', views.schedule_view, name='schedule_view'),
    path('registered-sessions/', views.registered_sessions_view, name='registered_sessions'),
    path('course-history/', views.course_history_view, name='course_history'),
    path('student/', views.student_view, name='student_view'),
    path('enrollment/', views.enrollment_view, name='enrollment_view'),
    path('register/<int:section_id>/', views.register, name='register'),
    path('dropcourse/<int:section_id>/', views.drop_course, name='drop_course'),
    path('course/<int:course_id>/', views.course_view, name='course_view'),
    path('faculty-directory/', views.faculty_directory, name='faculty_directory'),
    path('faculty/<str:user_id>/', views.faculty, name='faculty'),
    path('department-directory/', views.department_directory, name='department_directory'),
    path('major-directory/', views.major_directory, name='major_directory'),
    path('faculty/', views.faculty_view, name='faculty_view'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('events/', views.events_view, name='events_view'),

    path('admin/users/', views.admin_users_view, name='admin_users_view'),
    path('admin/courses/', views.admin_course_view, name='admin_course_view'),
    path('get_user_form/', views.get_user_form, name='get_user_form'),
    path('update_user/', views.update_user, name='update_user'),

]

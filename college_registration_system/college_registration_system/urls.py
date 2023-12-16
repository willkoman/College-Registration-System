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
    # path('/login/', views.user_login, name='user_login'),
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
    path('fac/search_student/', views.search_student_view, name='search_student'),
    path('admin/users/', views.admin_users_view, name='admin_users_view'),

    path('admin/courses/', views.admin_course_view, name='admin_course_view'),

    path('admin/add_course/', views.add_course, name='admin_add_course'),
    path('admin/update_course/<int:course_id>', views.edit_course, name='admin_update_course'),
    path('admin/delete_course/<int:course_id>', views.delete_course, name='admin_delete_course'),

    path('admin/course/<int:course_id>/sections/', views.admin_sections_view, name='admin_section_view'),
    path('admin/add_section/<int:course_id>', views.add_section, name='admin_add_section'),
    path('admin/update_section/<int:crn>', views.edit_section, name='admin_update_section'),
    path('admin/delete_section/<int:crn>', views.delete_section, name='admin_delete_section'),

    path('admin/students/', views.list_students_view, name='admin_students_view'),
    path('admin/student/holds/<int:student_id>', views.student_hold_view, name='admin_student_holds_view'),
    path('admin/student/holds/<int:student_id>/add/', views.add_student_hold, name='admin_add_student_holds'),
    path('admin/student/holds/<int:student_id>/delete/<int:hold_id>', views.delete_student_hold, name='admin_delete_student_holds'),
    path('admin/get_student_data/', views.get_student_data, name='admin_get_student_data'),
    path('admin/update_student/<int:student_id>', views.update_student_view, name='admin_update_student'),
    path('admin/student/gradebook/<int:student_id>', views.get_student_grades, name='admin_student_gradebook_view'),
    path('admin/student/gradebook/update/', views.update_gradebook_student, name='update_gradebook_student'),

    path('admin/facultys/', views.admin_faculty_view, name='admin_faculty_view'),
    path('admin/get_faculty_data/<str:user_id>', views.get_faculty_data, name='admin_get_faculty_data'),
    path('admin/update_faculty/<str:user_id>', views.update_faculty_view, name='admin_update_faculty'),

    path('admin/college/', views.admin_college_view, name='admin_college_view'),

    path('admin/manage_buildings/', views.manage_buildings, name='manage_buildings'),
    path('admin/manage_rooms/<int:building_id>/', views.manage_rooms, name='manage_rooms'),
    path('admin/addBuilding/', views.add_building, name='add_building'),
    path('admin/add_room/<int:building_id>', views.add_room, name='add_room'),


    path('get_user_form/', views.get_user_form, name='get_user_form'),
    path('update_user/', views.update_user, name='update_user'),
    path('add_user/', views.add_user, name='add_user'),
    path('delete_user/<str:user_id>', views.delete_user, name='delete_user'),

    path('gradebook/<int:section_id>/', views.gradebook_view, name='gradebook_view'),
    path('roster/<int:section_id>/', views.roster_view, name='roster_view'),
    path('attendance/<int:section_id>/', views.attendance_view, name='attendance_view'),
    path('update_attendance/<int:section_id>', views.update_attendance, name='update_attendance'),
    path('update_gradebook/', views.update_gradebook, name='update_gradebook'),

    path('degreeAudit/', views.degreeAudit_view, name='degreeAudit_view'),


    path('profile/', views.profile_view, name='profile_view'),
    path('update_profile/', views.update_profile, name='update_profile'),


    path('statisticsoffice/', views.statistics_view, name='statistics_view'),
    path('statisticsoffice/enrollment/', views.college_statistics_view, name='college_statistics_view'),

]

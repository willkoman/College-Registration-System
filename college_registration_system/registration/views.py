import datetime
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.db import transaction
from django.db.models import Sum
from .forms import CourseForm, CourseSectionForm, UserCompositeForm
from .models import (
    CoursePrereq,Attendance, Room, Semester,Hold, CourseSection,Department, Course,Login,
    Enrollment,Day,StudentHistory, Timeslot, User, Admin, Student, Faculty,Faculty_FullTime,
    Faculty_PartTime, Graduate,Grad_Full_Time,Grad_Part_Time,Undergrad_Full_Time,
    Undergrad_Part_Time, Undergraduate, Major,Minor, MajorDegreeRequirements,MinorDegreeRequirements
)
from django.contrib import messages
import requests
import json


add_drop_periods = Semester.objects.all().order_by('start_date')
#add_drop periods end 2 weeks after the start date of the semester and start 4 weeks before the start date of the semester
for period in add_drop_periods:
    period.add_drop_end_date = period.start_date + datetime.timedelta(days=14)
    period.add_drop_start_date = period.start_date - datetime.timedelta(days=48)
    period.save()
#region core
# @login_required(login_url='user_login')
def root_redirect(request):
    #if login that has that user is superuser, redirect to admin page
    # if request.user.is_authenticated:
    #     if request.user.is_superuser:
    #         return redirect('/admin/')

    return redirect('/homepage/')

def user_login(request):
    error_message = ''
    # Capture the 'next' parameter from the URL or set a default
    next_page = request.GET.get('next', '/homepage/')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_page = request.POST.get('next') or next_page
        if email and password:
            userlogin = authenticate(request, email=email, password=password)
        else:
            error_message = "Email and/or Password cannot be blank."
        print("Userlogin:", userlogin)

        if userlogin is not None:
            login(request, userlogin)
            try:
                print("User Type:", userlogin.user.user_type)
                if userlogin.user.user_type == 'Admin':
                    pass
                elif userlogin.user.user_type in ['Faculty', 'Student']:
                    if userlogin.is_locked:
                        error_message = "Your account is locked. Please contact the system administrator."
                        return render(request, 'login.html', {'error_message': error_message})

                userlogin.no_of_attempts = 0
                userlogin.save()

                # Redirect to 'next_page' if it exists, else redirect to homepage
                print("Next page:", next_page)
                return HttpResponseRedirect(next_page)
            except Exception as e:
                print("Exception:", e)
                error_message = "Error: User type not recognized."
        else:
            try:
                login_obj = Login.objects.get(email=email)
                if login_obj.no_of_attempts >= 3:
                    error_message = "You have exceeded the maximum number of login attempts. Please contact the system administrator."
                    login_obj.is_locked = True
                    login_obj.save()
                    return render(request, 'login.html', {'error_message': error_message,'next': next_page})

                login_obj.no_of_attempts += 1
                login_obj.save()
            except Login.DoesNotExist:
                pass
            error_message = "Invalid login credentials."
    return render(request, 'login.html', {'error_message': error_message,'next': next_page})

# @login_required(login_url='user_login')
def homepage(request):
    # Check if user is authenticated
    if request.user.is_authenticated:
        user = request.user.user
        username = user.first_name + ' ' + user.last_name
        usertype = user.user_type

        if usertype == 'Student':
            # Get student with that user and append to context
            student = Student.objects.get(user=user)
            context = {
                'username': username,
                'usertype': usertype,
                'student': student
            }

            try:
                context['grad'] = Graduate.objects.get(student=student)
            except Graduate.DoesNotExist:
                context['undergrad'] = Undergraduate.objects.get(student=student)
            print("Student:", student)  # Debugging line

        elif usertype == 'Faculty':
            # Get faculty with that user and append to context
            faculty = Faculty.objects.get(user=user)
            context = {
                'username': username,
                'usertype': usertype,
                'faculty': faculty
            }

            try:
                context['office'] = Faculty_FullTime.objects.get(faculty=faculty).office
            except Faculty_FullTime.DoesNotExist:
                context['office'] = Faculty_PartTime.objects.get(faculty=faculty).office
            print("Faculty:", faculty)

        else:
            context = {
                'username': username,
                'usertype': usertype,
            }

    else:
        context = {
            'username': "Visitor",
            'usertype': None,
        }

    return render(request, 'homepage.html', context)


def logout_view(request):
    logout(request)
    return redirect('/homepage/')

# @login_required(login_url='user_login')
def schedule_view(request):
    if request.user.is_authenticated:
        user = request.user.user
        username = user.first_name + ' ' + user.last_name
        usertype = user.user_type
    else:
        username = "Visitor"
        usertype = None

    context = {
        'username': username,
        'usertype': usertype,
    }
    course_sections = CourseSection.objects.all()
    formatted_sections = []

    for section in course_sections:
        timeslot = section.timeslot  # Assuming you have a ForeignKey to Timeslot in CourseSection
        days_str = ', '.join([str(day) for day in timeslot.days.all()])
        periods_str = ', '.join([f"{period.start_time} - {period.end_time}" for period in timeslot.periods.all()])

        formatted_sections.append({
            'crn': section.crn,
            'course': section.course,
            'section': section.crn,
            'timeslot': periods_str,
            'department' : section.course.department,
            'credits': section.course.no_of_credits,
            'days': days_str,
            'semester': section.semester,
            'room': str(section.room.building)+str(section.room.room_no),
            'faculty': section.faculty,
            'available_seats': int(section.available_seats),
        })

        context['departments'] = Department.objects.all()
        #context['timeslots'] = Timeslot.objects.all()
        context['semesters'] = Semester.objects.all()

    context['sections']=formatted_sections
    return render(request, 'schedule.html', context)


# @login_required(login_url='user_login')
def course_view(request,course_id):
    if request.user.is_authenticated:
        user = request.user.user
        username = user.first_name + ' ' + user.last_name
        usertype = user.user_type
    else:
        username = "Visitor"
        usertype = None

    context = {
        'username': username,
        'usertype': usertype,
    }
    course = Course.objects.get(course_id=course_id)
    context['course'] = course
    prereqs = CoursePrereq.objects.filter(course=course)
    context['prereqs'] = prereqs
    return render(request, 'course.html', context)
# @login_required(login_url='user_login')
def faculty_directory(request):
    # Retrieve all Faculty objects and their related Faculty_FullTime and Faculty_PartTime objects
    faculty = Faculty.objects.select_related('faculty_fulltime', 'faculty_parttime')
    if request.user.is_authenticated:
        user = request.user.user
        username = user.first_name + ' ' + user.last_name
        usertype = user.user_type
    else:
        username = "Visitor"
        usertype = None

    context = {
        'username': username,
        'usertype': usertype,
        'faculty': faculty,
    }
    return render(request, 'faculty_directory.html', context)
# @login_required(login_url='user_login')
def department_directory(request):
    if request.user.is_authenticated:
        user = request.user.user
        username = user.first_name + ' ' + user.last_name
        usertype = user.user_type
    else:
        username = "Visitor"
        usertype = None

    context = {
        'username': username,
        'usertype': usertype,
    }
    context['departments'] = Department.objects.all()
    return render(request, 'department_directory.html', context)
# @login_required(login_url='user_login')
def major_directory(request):
    if request.user.is_authenticated:
        user = request.user.user
        username = user.first_name + ' ' + user.last_name
        usertype = user.user_type
    else:
        username = "Visitor"
        usertype = None

    context = {
        'username': username,
        'usertype': usertype,
    }
    context['majors'] = Major.objects.all().distinct()
    return render(request, 'major_directory.html', context)

# @login_required(login_url='user_login')
def faculty(request,user_id):
    if request.user.is_authenticated:
        user = request.user.user
        username = user.first_name + ' ' + user.last_name
        usertype = user.user_type
    else:
        username = "Visitor"
        usertype = None

    context = {
        'username': username,
        'usertype': usertype,
    }
    faculty = Faculty.objects.get(user=user_id)
    context['faculty'] = faculty
    try:
        context['office'] = Faculty_FullTime.objects.get(faculty=faculty).office
    except:
        context['office'] = Faculty_PartTime.objects.get(faculty=faculty).office
    return render(request, 'faculty.html', context)

def get_holidays():
    api_key = "97NRjkRbLcWFblKOSf1zUdcJcDa5hYRh"
    country = "US"
    state = "NY"  # New York state code
    years = [2023, 2024]
    types = ["national", "local"]

    formatted_holidays = []
    unique_dates = set()

    for year in years:
        for holiday_type in types:
            url = f"https://calendarific.com/api/v2/holidays?api_key={api_key}&country={country}&year={year}&type={holiday_type}&location={state}"
            response = requests.get(url)
            holidays = response.json()
            if holiday_type == 'local':
                color= 'red'
            elif holiday_type == 'national':
                color= 'teal'
            else:
                color= 'gray'
            for holiday in holidays['response']['holidays']:
                date = holiday['date']['iso']
                if date not in unique_dates:
                    formatted_holidays.append({
                        'title': holiday['name'],
                        'start': date,
                        'color': color,
                    })
                    unique_dates.add(date)

    return formatted_holidays


def calendar_view(request):
    holidays = get_holidays()
    events = [
        {'title': 'Add Drop Starts For Fall 2023', 'start': str(add_drop_periods[0].add_drop_start_date)},
        {'title': 'Add Drop Ends For Fall 2023', 'start': str(add_drop_periods[0].add_drop_end_date)},
        {'title': 'Add Drop Starts For Spring 2024', 'start': str(add_drop_periods[1].add_drop_start_date)},
        {'title': 'Add Drop Ends for Spring 2024', 'start': str(add_drop_periods[1].add_drop_end_date)},
    ]
    for event in events:
        event['color'] = 'purple'
    combined_events = holidays + events  # Combine holidays and events

    context = {
        'events': json.dumps(combined_events)  # Convert to JSON
    }
    return render(request, 'calendar.html', context)

def events_view(request):
    # Example data - mock events
    events = [
        {"date": "2023-09-01", "event": "Fall Semester Begins"},
        {"date": str(add_drop_periods[0].add_drop_start_date), "event": "Fall Add/Drop Period Begins"},
        {"date": str(add_drop_periods[0].add_drop_end_date), "event": "Fall Add/Drop Period Ends"},
        {"date": str(add_drop_periods[1].add_drop_start_date), "event": "Spring Add/Drop Period Ends"},
        {"date": str(add_drop_periods[1].add_drop_end_date), "event": "Spring Add/Drop Period Ends"},
        {"date": "2023-09-05", "event": "Labor Day - No Classes"},
        {"date": "2023-10-15", "event": "Midterm Exams Week"},
        {"date": "2023-11-24", "event": "Thanksgiving Break"},
        {"date": "2023-12-08", "event": "Final Exams Week"},
        {"date": "2023-12-15", "event": "Fall Semester Ends"},
        {"date": "2024-01-10", "event": "Spring Semester Begins"},
        {"date": "2024-03-01", "event": "Spring Break"},
        {"date": "2024-05-15", "event": "Final Exams Week"},
        {"date": "2024-05-30", "event": "Commencement Ceremony"}
    ]
    context = {
        'events': events
    }
    return render(request, 'events.html', context)


#endregion
#region student
#### STUDENT VIEWS ####
@login_required(login_url='user_login')
def registered_sessions_view(request):
    if not request.user.user.user_type == 'Student':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    student = request.user.student  # Assuming you have a ForeignKey from User to Student
    registered_sessions = Enrollment.objects.filter(student=student)
    return render(request, 'registered_sessions.html', {'registered_sessions': registered_sessions})

@login_required(login_url='user_login')
def course_history_view(request):
    if not request.user.user.user_type == 'Student':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    student = Student.objects.get(user=request.user.user)
    context['course_history'] = StudentHistory.objects.filter(student=student)
    return render(request, 'course_history.html',context)


@login_required(login_url='user_login')
def student_view(request):
    if not request.user.user.user_type == 'Student':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    user = request.user.user
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    if request.user.user.user_type == 'Student':
        #get student with that user and append to context
        context['student'] = Student.objects.get(user=user)

        try:
            context['grad'] = Graduate.objects.get(student=context['student'])
        except:
            context['undergrad'] = Undergraduate.objects.get(student=context['student'])
        print("Student:", context['student'])  # Debugging line
        context['enrollment'] = Enrollment.objects.filter(student=context['student'])
        context['student_history'] = StudentHistory.objects.filter(student=context['student'])

    elif request.user.user.user_type == 'Faculty':
        #get faculty with that user and append to context
        context['faculty'] = Faculty.objects.get(user=user)
        try:
            context['office'] = Faculty_FullTime.objects.get(faculty=context['faculty']).office
        except:
            context['office'] = Faculty_PartTime.objects.get(faculty=context['faculty']).office

        print("Faculty:", context['faculty'])
    return render(request, 'student_page.html', context)

@login_required(login_url='user_login')
def enrollment_view(request):
    if not request.user.user.user_type == 'Student':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    student = request.user.user.student
    enrollments = Enrollment.objects.filter(student=student).select_related('section', 'section__course', 'section__timeslot').prefetch_related('section__timeslot__days')

    # Prepare a dictionary to map weekdays to FullCalendar indices
    weekday_to_index = {
        'Sunday': 0,
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6,
    }

    # For each enrollment, get the day indices
    for enrollment in enrollments:
        days = enrollment.section.timeslot.days.all()
        day_indices = [weekday_to_index[day.weekday] for day in days]
        enrollment.day_indices = day_indices  # Assign the indices list to the enrollment object

    context = {
        'username': request.user.user.first_name + ' ' + request.user.user.last_name,
        'usertype': request.user.user.user_type,
        'enrollment': enrollments,
    }


    return render(request, 'enrollment.html', context)

@login_required(login_url='user_login')
def register(request, section_id):
    if not request.user.user.user_type == 'Student':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/schedule/')
    #distionary assigning number to grade
    grade_dict = {'A':4,'A-':3.5,'B+':3.25,'B':3,'B-':2.75,'C+':2.25,'C':2,'C-':1.75,'D+':1.25,'D':1,'D-':0.75,'F':0,'NA':0}
    try:
        student = request.user.user.student
        section = CourseSection.objects.get(crn=section_id)
        enrollment = Enrollment(student=student, section=section, date_of_enrollment=datetime.date.today(), grade='NA')

        '''All the checks for registration'''

        # if enrollment already exists with the student and same section, raise an exception
        if Enrollment.objects.filter(student=student, section=section).exists():
            raise Exception("You have already registered for this section.")
        if Enrollment.objects.filter(student=student).count() >= 4:
            raise Exception("You have already registered for 4 courses in this semester.")
        #if same timeslot in coursesection already in enrollment, raise exception
        if Enrollment.objects.filter(student=student, section__timeslot=section.timeslot).exists():
            if section.semester == Enrollment.objects.get(student=student, section__timeslot=section.timeslot).section.semester:
                raise Exception("You have already registered for a course in this timeslot for this semester.")
        #if student has completed course already with grade C or higher, raise exception
        if Enrollment.objects.filter(student=student, section__course=section.course).exists():
            raise Exception("You are already registered for this course.")
        if StudentHistory.objects.filter(student=student, section__course=section.course).exists():
            if grade_dict[StudentHistory.objects.get(student=student, section__course=section.course).grade] >= grade_dict['C']:
                raise Exception("You have already completed this course.")
        if CoursePrereq.objects.filter(course=section.course).exists():
            prereqs = CoursePrereq.objects.filter(course=section.course)
            for prereq in prereqs:
                if not StudentHistory.objects.filter(student=student, section__course=prereq.pr_course).exists():
                    raise Exception(f"You have not completed the prerequisite course: {prereq.pr_course}")
                elif grade_dict[StudentHistory.objects.get(student=student, section__course=prereq.pr_course).grade] < grade_dict[prereq.min_grade]:
                    raise Exception(f"You have not achieved a high enough grade for: {prereq.pr_course}")
        if Hold.objects.filter(student=student).exists():
            holdTypes = Hold.objects.filter(student=student)
            #get unique hold types
            holdTypes = set([hold.hold_type for hold in holdTypes])
            holdTypes_str = ', '.join(holdTypes)
            raise Exception(f"You have the following hold(s) on your account:\n{holdTypes_str}.\nPlease contact the system administrator.")
        #if course.semester is the first semester, then it is add_drop_periods[0], else it is add_drop_periods[1]
        #TODO: UNCOMMENT WHEN NO LONGER TESTING
        semes = section.semester
        semes = add_drop_periods[0] if semes == add_drop_periods[0] else add_drop_periods[1]
        if datetime.date.today() > semes.add_drop_end_date:
            raise Exception(f"Add/Drop period for {section.semester} has ended. The period is {semes.add_drop_start_date} - {semes.add_drop_end_date}")
        if datetime.date.today() < semes.add_drop_start_date:
            raise Exception(f"Add/Drop period for {section.semester} has not started yet. The period is {semes.add_drop_start_date} - {semes.add_drop_end_date}")
        '''All checks passed, save enrollment'''
                #if student has registered for more than 2 courses this semester, they are now a fulltime student
        if Enrollment.objects.filter(student=student, section__semester=section.semester).count() > 2:
            if student.student_type == 'Undergraduate':
                #get undergrad object and change to fulltime
                undergrad = Undergraduate.objects.get(student=student)
                undergrad.undergrad_student_type = 'Fulltime'
                undergrad.save()
            elif student.student_type == 'Graduate':
                #get grad object and change to fulltime
                grad = Graduate.objects.get(student=student)
                grad.grad_student_type = 'Fulltime'
                grad.save()
        enrollment.save()
        # Add a success message
        messages.success(request, f'You have successfully registered for {section}!',extra_tags='Success')
    except Exception as e:
        print("Exception:", e)
        # Add a failure message
        messages.error(request, f'An error occurred while registering for {section}.\n{e}',extra_tags='Error')
    return redirect('/schedule/')

@login_required(login_url='user_login')
def drop_course(request,section_id):
    if not request.user.user.user_type == 'Student':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/enrollment/')
    try:
        student = request.user.user.student
        section = CourseSection.objects.get(crn=section_id)
        enrollment = Enrollment.objects.get(student=student, section=section)
        enrollment.delete()
        # Add a success message
        messages.success(request, f'You have successfully dropped {section}!',extra_tags='Success')

        if Enrollment.objects.filter(student=student, section__semester=section.semester).count() <= 2:
            if student.student_type == 'Undergraduate':
                #get undergrad object and change to parttime
                undergrad = Undergraduate.objects.get(student=student)
                undergrad.undergrad_student_type = 'Parttime'
                undergrad.save()
            elif student.student_type == 'Graduate':
                #get grad object and change to parttime
                grad = Graduate.objects.get(student=student)
                grad.grad_student_type = 'Parttime'
                grad.save()

    except Exception as e:
        print("Exception:", e)
        # Add a failure message
        messages.error(request, f'An error occurred while dropping {section}.\n{e}',extra_tags='Error')
    return redirect('/enrollment/')

@login_required(login_url='user_login')
def degreeAudit_view(request):
    if not request.user.user.user_type == 'Student':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/homepage/')

    student = Student.objects.get(user=request.user.user)
    context = {
        'username': request.user.user.first_name + ' ' + request.user.user.last_name,
        'usertype': request.user.user.user_type,
        'student': student,
    }

    # Adding Undergraduate or Graduate information
    if student.student_type == 'Undergraduate':
        context['undergrad_info'] = Undergraduate.objects.get(student=student)
    elif student.student_type == 'Graduate':
        context['grad_info'] = Graduate.objects.get(student=student)

    # Major and Minor Degree Requirements
    if student.major_id:
        major_reqs = MajorDegreeRequirements.objects.get(major=student.major_id)
        context['major_reqs'] = major_reqs
    if student.minor_id:
        minor_reqs = MinorDegreeRequirements.objects.get(minor=student.minor_id)
        context['minor_reqs'] = minor_reqs
    #get courses from course sections in studenthistory
    context['inprogress_courses'] = Enrollment.objects.filter(student=student)
    context['inprogress_courses'] = [course.section.course for course in context['inprogress_courses']]
    context['completed_courses'] = StudentHistory.objects.filter(student=student)
    #completed courses are not currently in progress
    context['completed_courses'] = [course.section.course for course in context['completed_courses'] if course.section.course not in context['inprogress_courses']]
    print("Inprogress Courses:", context['inprogress_courses'])
    print("Completed Courses:", context['completed_courses'])

    # Calculate credits
    context['completed_credits'], context['inprogress_credits'] = calculate_credits(student)

    return render(request, 'degreeAudit.html', context)

def calculate_credits(student):
    completed_credits = 0
    inprogress_credits = 0
    enrollments = StudentHistory.objects.filter(student=student)
    for enrollment in enrollments:
        course_credits = enrollment.section.course.no_of_credits
        if enrollment.grade and enrollment.grade not in ['F', 'NA']:
            completed_credits += course_credits
        elif enrollment.grade == 'NA':
            inprogress_credits += course_credits
    return completed_credits, inprogress_credits

#endregion
#region admin
#### ADMIN VIEWS ####
@login_required(login_url='user_login')
def admin_view(request):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
        'admin': Admin.objects.get(user=request.user.user),
    }
    #get admin_view.html from templates/admin
    return render(request, 'admin/admin_view.html', context)

@login_required(login_url='user_login')
def admin_users_view(request, user_id=None):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    user = None
    if user_id:
        user = User.objects.get(id=user_id)
        form = UserCompositeForm(instance=user)
    else:
        form = UserCompositeForm()

    if request.method == 'POST':
        form = UserCompositeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            # Redirect to user list or detail view
            return redirect('admin_users_view')

    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
        'form': form,
        'users': User.objects.all().select_related('student', 'faculty', 'admin', 'login'),
        'holds': Hold.objects.all(),
        # ... other context data ...
    }
    return render(request, 'admin/admin_users.html', context)

def get_user_form(request):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/homepage/')
    user_id = request.GET.get('user_id')
    user = User.objects.get(id=user_id)
    form = UserCompositeForm(instance=user)

    # Assuming you're using Django templates, render the form to a template,
    # or find another way to split the form fields based on user type.
    return render(request, 'partials/edituser.html', {'form': form})

@login_required(login_url='user_login')
def update_user(request):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/homepage/')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_type = request.POST.get('user_type')
        print("User ID:", user_id)

        user = get_object_or_404(User, id=user_id)
        form = UserCompositeForm(request.POST, instance=user)

        if form.is_valid():
            user_instance = form.save()

            if user_type == 'Student':
                student, created = Student.objects.get_or_create(user=user_instance)
                student.studentID = form.cleaned_data.get('studentID')
                student.major_id = form.cleaned_data.get('major_id')
                student.minor_id = form.cleaned_data.get('minor_id')
                student.enrollment_year = form.cleaned_data.get('enrollment_year')
                student.student_type = form.cleaned_data.get('student_type')
                student.save()
            elif user_type == 'Faculty':
                faculty, created = Faculty.objects.get_or_create(user=user_instance)
                faculty.rank = form.cleaned_data.get('rank')
                faculty.departments.set(form.cleaned_data.get('departments'))
                faculty.specialty = form.cleaned_data.get('specialty')
                faculty.fac_type = form.cleaned_data.get('fac_type')
                faculty.save()
            elif user_type == 'Admin':
                admin, created = Admin.objects.get_or_create(user=user_instance)
                admin.access_level = form.cleaned_data.get('access_level')
                admin.save()

            messages.success(request, 'User edited successfully.')
            return JsonResponse({'status': 'success', 'redirect_url': '/admin/users/'})
        else:
            messages.error(request, 'Error: User could not be edited.')
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


    return JsonResponse({'status': 'method not allowed'}, status=405)

@login_required(login_url='user_login')
def add_user(request):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/homepage/')
    if request.method == 'POST':
        form = UserCompositeForm(request.POST)
        if form.is_valid():
            user_instance = form.save()
            user_type = form.cleaned_data.get('user_type')

            if user_type == 'Student':
                student, created = Student.objects.get_or_create(user=user_instance)
                student.studentID = form.cleaned_data.get('studentID')
                student.major_id = form.cleaned_data.get('major_id')
                student.minor_id = form.cleaned_data.get('minor_id')
                student.enrollment_year = form.cleaned_data.get('enrollment_year')
                student.student_type = form.cleaned_data.get('student_type')
                student.save()
            elif user_type == 'Faculty':
                faculty, created = Faculty.objects.get_or_create(user=user_instance)
                faculty.rank = form.cleaned_data.get('rank')
                faculty.departments.set(form.cleaned_data.get('departments'))
                faculty.specialty = form.cleaned_data.get('specialty')
                faculty.fac_type = form.cleaned_data.get('fac_type')
                faculty.save()
            elif user_type == 'Admin':
                admin, created = Admin.objects.get_or_create(user=user_instance)
                admin.access_level = form.cleaned_data.get('access_level')
                admin.save()

            messages.success(request, 'User added successfully.')
            return JsonResponse({'status': 'success', 'redirect_url': '/admin/users/'})
        else:
            messages.error(request, 'Error: User could not be added.')
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'status': 'method not allowed'}, status=405)
@login_required(login_url='user_login')
def admin_course_view(request):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    context['departments'] = Department.objects.all()
    context['courses'] = Course.objects.all()
    return render(request, 'admin/admin_courses.html', context)

@login_required(login_url='user_login')
def add_course(request):
    if not request.user.user.user_type == 'Admin':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course {form.cleaned_data.get("course_name")} added successfully.',extra_tags='Success')
            return JsonResponse({'status': 'success', 'message': 'Course added successfully', 'redirect_url': '/admin/courses/'})
        else:
            print(form.errors)
            messages.error(request, f'Error: Course could not be added.', extra_tags='Error')
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@login_required(login_url='user_login')
def edit_course(request, course_id):
    if not request.user.user.user_type == 'Admin':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)

    course = get_object_or_404(Course, course_id=course_id)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course {form.cleaned_data.get("course_name")} edited successfully.', extra_tags='Success')
            return JsonResponse({'status': 'success', 'message': 'Course edited successfully', 'redirect_url': '/admin/courses/'})
        else:
            print(form.errors)
            messages.error(request, f'Error: Course could not be edited.', extra_tags='Error')
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required(login_url='user_login')
def delete_course(request,course_id):
    if not request.user.user.user_type == 'Admin':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)
    course = Course.objects.get(course_id=course_id)
    sessions = CourseSection.objects.filter(course=course)
    #if any sections have more than 4 students, return error message
    for session in sessions:
        if Enrollment.objects.filter(section=session).count() > 4:
            messages.error(request, f'Error: Course {session} has more than 4 students enrolled.', extra_tags='Error')
            return JsonResponse({'status': 'error', 'message': f'Course {session} has more than 4 students enrolled.'}, status=400)
    #delete all sections
    for session in sessions:
        session.delete()
    #delete course

    course.delete()
    messages.success(request, f'Course {course} deleted successfully.', extra_tags='Success')

    return JsonResponse({'status': 'success', 'message': f'Course {course} deleted successfully.'})

@login_required(login_url='user_login')
def admin_sections_view(request, course_id):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    context['course'] = Course.objects.get(course_id=course_id)
    context['sections'] = CourseSection.objects.filter(course=context['course'])
    context['timeslots'] = Timeslot.objects.all()
    context['rooms'] = Room.objects.all()
    context['semesters'] = Semester.objects.all()
    context['available_faculty'] = []
    availFac = Faculty.objects.filter(departments=context['course'].department)
    for faculty in availFac:
        if faculty.fac_type == 'Fulltime':
            #add any faculty_fulltime where num_of_courses < 2
            if Faculty_FullTime.objects.get(faculty=faculty).num_of_courses < 2:
                context['available_faculty'].append(faculty)
        else:
            #add any faculty_parttime where num_of_courses < 1
            if Faculty_PartTime.objects.get(faculty=faculty).num_of_courses < 1:
                context['available_faculty'].append(faculty)
    return render(request, 'admin/admin_course_sections.html', context)

@login_required(login_url='user_login')
def add_section(request, course_id):
    if not request.user.user.user_type == 'Admin':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)

    if request.method == 'POST':
        form = CourseSectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Section {form.cleaned_data.get("crn")} added successfully.',extra_tags='Success')
            return JsonResponse({'status': 'success', 'message': 'Section added successfully', 'redirect_url': '/admin/courses/'})
        else:
            print(form.errors)
            messages.error(request, f'Error: Section could not be added.', extra_tags='Error')
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required(login_url='user_login')
def edit_section(request, crn):
    if not request.user.user.user_type == 'Admin':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)

    section = get_object_or_404(CourseSection, crn=crn)

    if request.method == 'POST':
        form = CourseSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, f'Section {form.cleaned_data.get("crn")} edited successfully.', extra_tags='Success')
            return JsonResponse({'status': 'success', 'message': 'Section edited successfully', 'redirect_url': '/admin/courses/'})
        else:
            print(form.errors)
            messages.error(request, f'Error: Section could not be edited.', extra_tags='Error')
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@login_required(login_url='user_login')
def delete_section(request,crn):
    if not request.user.user.user_type == 'Admin':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)
    section = CourseSection.objects.get(crn=crn)
    #if section has more than 4 students, return error message
    if Enrollment.objects.filter(section=section).count() > 4:
        messages.error(request, f'Error: Section {section} has more than 4 students enrolled.', extra_tags='Error')
        return JsonResponse({'status': 'error', 'message': f'Section {section} has more than 4 students enrolled.'}, status=400)
    #delete section
    section.delete()
    messages.success(request, f'Section {section} deleted successfully.', extra_tags='Success')

    return JsonResponse({'status': 'success', 'message': f'Section {section} deleted successfully.'})
#endregion
#region faculty
#### FACULTY VIEWS ####

@login_required(login_url='user_login')
def faculty_view(request):
    if not request.user.user.user_type == 'Faculty':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    fac = Faculty.objects.select_related('faculty_fulltime', 'faculty_parttime').filter(user=request.user.user)[0]

    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
        'faculty': fac,
    }
    context['courses'] = CourseSection.objects.filter(faculty=fac)
    context['manager'] = Department.objects.filter(manager_id=fac)

    if context['manager'].exists():
        #get major in department
        context['major'] = Major.objects.filter(department=context['manager'][0])
        #get all students in major
        students = Student.objects.filter(major_id=context['major'][0])
        #attach email to each student from login to context
        context['students'] = []
        for student in students:
            student_course_history = StudentHistory.objects.filter(student=student)
            context['students'].append({'student': student, 'email': Login.objects.get(user=student.user).email,'course_history': student_course_history})

    return render(request, 'faculty_view.html', context)
@login_required(login_url='user_login')
def gradebook_view(request, section_id):
    if not request.user.user.user_type == 'Faculty':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/homepage/')
    print("Section ID:", section_id)
    section = CourseSection.objects.get(crn=section_id)
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
        'section': section,
    }
    context['enrollments'] = Enrollment.objects.filter(section=section)
    return render(request, 'faculty/gradebook.html', context)
@login_required(login_url='user_login')
def update_gradebook(request):
    #recieve a list of enrollments and update the grades
    if not request.user.user.user_type == 'Faculty':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/homepage/')
    if request.method == 'POST':
        enrollments = request.POST.getlist('enrollments[]')
        grades = request.POST.getlist('grades[]')
        for enrollment, grade in zip(enrollments, grades):
            enrollment = Enrollment.objects.get(id=enrollment)
            enrollment.grade = grade
            enrollment.save()
        messages.success(request, f'Grades updated successfully.',extra_tags='Success')
        print("gradebook/"+str(enrollment.section.crn))
        return JsonResponse({'status': 'success','redirect_url': '/gradebook/'+str(enrollment.section.crn)})
    else:
        messages.error(request, f'An error occurred while updating grades.',extra_tags='Error')
        return JsonResponse({'status': 'error'}, status=400)

@login_required(login_url='user_login')
def roster_view(request, section_id):
    if not request.user.user.user_type == 'Faculty':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/homepage/')
    section = CourseSection.objects.get(crn=section_id)
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
        'section': section,
    }

    enrollments = Enrollment.objects.filter(section=section)
    context['enrollments'] = []
    for enrollment in enrollments:
        #attach student email to enrollment
        context['enrollments'].append({'enrollment': enrollment, 'email': Login.objects.get(user=enrollment.student.user).email})

    return render(request, 'faculty/roster.html', context)

def parse_date(date_str):
    date_parts = date_str.split('-')
    return datetime.date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))

@login_required(login_url='user_login')
def attendance_view(request, section_id):
    if not request.user.user.user_type == 'Faculty':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/homepage/')
    section = CourseSection.objects.get(crn=section_id)
    date_str = request.GET.get('date')
    date = parse_date(date_str) if date_str else None
    enrollments = Enrollment.objects.filter(section=section)
    attendances = {}
    print("Selected Date:", date)
    if date:
        for attendance in Attendance.objects.filter(section=section, date_of_class=date):
            attendances[attendance.student.studentID] = attendance.present

    print("Attendances Dictionary:", attendances)  # Add this line to debug

    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
        'section': section,
        'date': date,
        'attendances': attendances,
        'enrollments': enrollments,
        'selected_date': request.POST.get('date_of_class', datetime.date.today().strftime("%Y-%m-%d"))  # Default to today's date
    }

    return render(request, 'faculty/attendance.html', context)
@login_required(login_url='user_login')
def update_attendance(request, section_id):
    if not request.user.user.user_type == 'Faculty':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/homepage/')
    if request.method == 'POST':
        date_of_class = request.POST.get('date_of_class')
        attendances = request.POST.getlist('attendances[]')

        for student_id in attendances:
            present_value = f'present_{student_id}' in request.POST
            student = Student.objects.get(studentID=student_id)
            section = CourseSection.objects.get(crn=section_id)
            # course = section.course
            #find attendance object with student, section, course, and date_of_class, if it exists, delete it
            try:
                attendance, created = Attendance.objects.get(
                    student=student,
                    section=section,
                    # course=course,
                    date_of_class=date_of_class
                ).delete()
            except:
                pass
            attendance, created = Attendance.objects.get_or_create(
                student=student,
                section=section,
                # course=course,
                present=present_value,
                date_of_class=date_of_class
            )
            attendance.save()

        messages.success(request, 'Attendance updated successfully.',extra_tags='Success')
        return JsonResponse({'status': 'success','redirect_url': '/attendance/'+str(section_id)})

    else:
        messages.error(request, 'An error occurred while updating attendance.')
        return JsonResponse({'status': 'error','redirect_url':'/attendance/'+str(section_id)}, status=400)

#endregion
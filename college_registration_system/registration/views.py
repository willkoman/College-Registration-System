import datetime
import random
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.core.serializers import serialize
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import BuildingForm, CourseForm, CourseSectionForm, FacultyEditForm, RoomForm, StudentEditForm, UserCompositeForm
from .models import (
    Building, CoursePrereq,Attendance, Room, Semester,Hold, CourseSection,Department, Course,Login,
    Enrollment,Day,StudentHistory, Timeslot, User, Admin, Student, Faculty,Faculty_FullTime,
    Faculty_PartTime, Graduate,Grad_Full_Time,Grad_Part_Time,Undergrad_Full_Time,
    Undergrad_Part_Time, Undergraduate, Major,Minor, MajorDegreeRequirements,MinorDegreeRequirements,
    StatisticsOffice
)
from django.contrib import messages
import requests
import json


add_drop_periods = Semester.objects.all().order_by('start_date')
grade_dict = {'A':4,'A-':3.5,'B+':3.25,'B':3,'B-':2.75,'C+':2.25,'C':2,'C-':1.75,'D+':1.25,'D':1,'D-':0.75,'F':0,'NA':0}
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

    context['email'] = Login.objects.get(user=faculty.user).email
    # context['phone'] = faculty.user.phone
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
        {'title': 'Add Drop Starts For Fall 2023', 'start': str(Semester.objects.get(semester_name='Fall 2023').add_drop_start_date)},
        {'title': 'Add Drop Ends For Fall 2023', 'start': str(Semester.objects.get(semester_name='Fall 2023').add_drop_end_date)},
        {'title': 'Add Drop Starts For Spring 2024', 'start': str(Semester.objects.get(semester_name='Spring 2024').add_drop_start_date)},
        {'title': 'Add Drop Ends for Spring 2024', 'start': str(Semester.objects.get(semester_name='Spring 2024').add_drop_end_date)},
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
        {"date": Semester.objects.get(semester_name="Fall 2023").add_drop_start_date, "event": "Fall Add/Drop Period Begins"},
        {"date": Semester.objects.get(semester_name="Fall 2023").add_drop_end_date, "event": "Fall Add/Drop Period Ends"},
        {"date": Semester.objects.get(semester_name='Spring 2024').add_drop_start_date, "event": "Spring Add/Drop Period Ends"},
        {"date": Semester.objects.get(semester_name='Spring 2024').add_drop_end_date, "event": "Spring Add/Drop Period Ends"},
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

@login_required(login_url='user_login')
def profile_view(request):
    if not request.user.is_authenticated:
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    else:
        user = request.user.user
        username = user.first_name + ' ' + user.last_name
        usertype = user.user_type

    context = {
        'username': username,
        'usertype': usertype,
    }
    context['user'] = user
    context['login'] = Login.objects.get(user=user)
    return render(request, 'profile.html', context)

@login_required(login_url='user_login')
def update_profile(request):
    if request.method == 'POST':
        user = request.user.user
        user.street = request.POST.get('street')
        user.city = request.POST.get('city')
        user.state = request.POST.get('state')
        user.zip_code = request.POST.get('zip_code')
        user.save()

        # Handling password change
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if old_password and new_password and confirm_password:
            userlogin = request.user
            if check_password(old_password, userlogin.password):
                if new_password == confirm_password:
                    userlogin.set_password(new_password)
                    userlogin.save()
                    update_session_auth_hash(request, userlogin)
                    messages.success(request, 'Your password was successfully updated!')
                else:
                    messages.error(request, 'New passwords do not match.')
            else:
                messages.error(request, 'Old password is incorrect.')

        messages.success(request, 'Your profile was successfully updated!')
        return redirect('profile_view')
    else:
        return render(request, 'profile.html')
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
        context['holds'] = Hold.objects.filter(student=context['student'])

        #if student has registered for more than 2 courses this semester, they are now a fulltime student
        if (Enrollment.objects.filter(student=context['student'], section__semester=Semester.objects.get(semester_name='Fall 2023')).count() > 2) or \
            (Enrollment.objects.filter(student=context['student'], section__semester=Semester.objects.get(semester_name='Spring 2024')).count() > 2):
            if context['student'].student_type == 'Undergraduate':
                #get undergrad object and change to fulltime
                undergrad = Undergraduate.objects.get(student=context['student'])
                undergrad.undergrad_student_type = 'Fulltime'
                undergrad.save()
                context['undergrad'] = undergrad
            elif context['student'].student_type == 'Graduate':
                #get grad object and change to fulltime
                grad = Graduate.objects.get(student=context['student'])
                grad.grad_student_type = 'Fulltime'
                grad.save()
                context['grad'] = grad
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
    #if enrollment is past the add_drop period, then it is not deletable
    for i, enrollment in enumerate(context['enrollment']):
        print(enrollment.section.semester)
        is_fall_2023 = enrollment.section.semester.semester_name == "Fall 2023"
        is_spring_2024 = enrollment.section.semester.semester_name == "Spring 2024"

        if (is_fall_2023 and datetime.date.today() > Semester.objects.get(semester_name='Fall 2023').add_drop_end_date) or \
        (is_spring_2024 and datetime.date.today() > Semester.objects.get(semester_name='Spring 2024').add_drop_end_date):
            enrollment.is_deletable = False
        else:
            enrollment.is_deletable = True

        #if it is not either fall 2023 or spring 2024, then it is not deletable
        if not (is_fall_2023 or is_spring_2024):
            enrollment.is_deletable = False


    return render(request, 'enrollment.html', context)

@login_required(login_url='user_login')
def register(request, section_id):
    if not request.user.user.user_type == 'Student':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/schedule/')
    #distionary assigning number to grade

    try:
        student = request.user.user.student
        section = CourseSection.objects.get(crn=section_id)
        enrollment = Enrollment(student=student, section=section, date_of_enrollment=datetime.date.today(), grade='NA')

        '''All the checks for registration'''
        #If semester add drop is over, raise exception
        semes = section.semester
        #if semester is not fall 2023 or spring 2024, raise exception
        if semes.semester_name not in ['Fall 2023', 'Spring 2024']:
            raise Exception(f"Registration is not available for {section.semester}.")
        # semes = add_drop_periods[0] if semes == add_drop_periods[0] else add_drop_periods[1]
        semes = Semester.objects.get(semester_name=semes.semester_name)
        if datetime.date.today() > semes.add_drop_end_date:
            raise Exception(f"Add/Drop period for {section.semester} has ended. The period is {semes.add_drop_start_date} - {semes.add_drop_end_date}")
        if datetime.date.today() < semes.add_drop_start_date:
            raise Exception(f"Add/Drop period for {section.semester} has not started yet. The period is {semes.add_drop_start_date} - {semes.add_drop_end_date}")
        #if student has completed course already with grade C or higher, raise exception
        if Enrollment.objects.filter(student=student, section__course=section.course).exists():
            raise Exception("You are already registered for this course.")
        if StudentHistory.objects.filter(student=student, section__course=section.course).exists():
            if grade_dict[StudentHistory.objects.get(student=student, section__course=section.course).grade] >= grade_dict['C']:
                raise Exception("You have already completed this course.")
        # if enrollment already exists with the student and same section, raise an exception
        if Enrollment.objects.filter(student=student, section=section).exists():
            raise Exception("You have already registered for this section.")
        if Enrollment.objects.filter(student=student).count() >= 4:
            #only 4 max per semester
            if Enrollment.objects.filter(student=student, section__semester=section.semester).count() >= 4:

                raise Exception("You have already registered for 4 courses in this semester.")
        #if same timeslot in coursesection already in enrollment, raise exception
        if Enrollment.objects.filter(student=student, section__timeslot=section.timeslot).exists():
            if section.semester == Enrollment.objects.get(student=student, section__timeslot=section.timeslot).section.semester:
                raise Exception("You have already registered for a course in this timeslot for this semester.")

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
        #TODO: UNCOMMENT WHEN NO LONGER TESTING
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
    context['not_good_courses'] = []
    context['completed_courses'] = StudentHistory.objects.filter(student=student)
    #completed courses are not currently in progress
    context['completed_courses'] = [course.section.course for course in context['completed_courses'] if course.section.course not in context['inprogress_courses']]
    grade_order = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C']

    for course in list(context['completed_courses']):  # Create a copy of the list to iterate over
        # Fetch all grades for this course
        grades = StudentHistory.objects.filter(student=student, section__course=course).values_list('grade', flat=True)

        # Find the highest grade
        highest_grade = max(grades, key=lambda grade: grade_order.index(grade) if grade in grade_order else -1)

        # Check if the highest grade is lower than a C
        if highest_grade not in grade_order:
            context['not_good_courses'].append(course)
            context['completed_courses'].remove(course)

    print("Inprogress Courses:", context['inprogress_courses'])
    print("Completed Courses:", context['completed_courses'])
    print("Not Good Courses:", context['not_good_courses'])
    # Calculate credits
    context['completed_credits'], context['inprogress_credits'] = calculate_credits(student)

    return render(request, 'degreeAudit.html', context)

def calculate_credits(student):
    completed_credits = 0
    inprogress_credits = 0
    enrollments = StudentHistory.objects.filter(student=student)
    for enrollment in enrollments:
        course_credits = enrollment.section.course.no_of_credits
        if enrollment.grade and enrollment.grade not in ['C-','D+','D','D-','F', 'NA']:
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
def delete_user(request, user_id):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to access this resource.',extra_tags='Error')
        return redirect('/homepage/')
    user = User.objects.get(id=user_id)
    user.delete()
    messages.success(request, 'User deleted successfully.')
    return JsonResponse({'status': 'success', 'message': 'User deleted successfully.'})

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
        if faculty.fac_type == 'FullTime':
            #add any faculty_fulltime where num_of_courses < 2
            if Faculty_FullTime.objects.get(faculty=faculty).num_of_courses < 2:
                context['available_faculty'].append(faculty)
        elif faculty.fac_type == 'PartTime':
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
            #add course_id to form
            form.instance.course = Course.objects.get(course_id=course_id)
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

@login_required(login_url='user_login')
def list_students_view(request):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, "You are not authorized to view this page.")
        return redirect('/homepage/')

    students = Student.objects.all()

    for student in students:
        if student.student_type == 'Undergraduate':
            undergrad_record = Undergraduate.objects.filter(student=student).first()
            if undergrad_record:
                student.time_status = undergrad_record.undergrad_student_type
            else:
                student.time_status = 'Unknown'
        elif student.student_type == 'Graduate':
            grad_record = Graduate.objects.filter(student=student).first()
            if grad_record:
                student.time_status = grad_record.grad_student_type
            else:
                student.time_status = 'Unknown'

    context = {
        'username': request.user.user.first_name + ' ' + request.user.user.last_name,
        'usertype': request.user.user.user_type,
        'students': students,
    }

    return render(request, 'admin/admin_students.html', context)
@login_required(login_url='user_login')
def get_student_data(request):
    if not request.user.user.user_type == 'Admin':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)
    #get student_id from request
    student_id = request.GET.get('studentID')
    student = get_object_or_404(Student, studentID=student_id)
    data = {
        'studentID': student.studentID,
        'first_name': student.user.first_name,
        'last_name': student.user.last_name,
        'major_id': student.major_id.id if student.major_id else None,
        'minor_id': student.minor_id.id if student.minor_id else None,
        'enrollment_year': student.enrollment_year,
        'student_type': student.student_type,
        # Add additional fields as needed
    }

    majors = {str(major.id): major.major_name for major in Major.objects.all()}
    minors = {str(minor.id): minor.minor_name for minor in Minor.objects.all()}
    departments = {str(department.department_id): department.department_name for department in Department.objects.all()}
    # Add a 'None' option
    majors[''] = 'None'
    minors[''] = 'None'
    departments[''] = 'None'
    # Ensure the selected value is a string since JavaScript expects string keys
    data['major_id'] = str(student.major_id.id if student.major_id else '')
    data['minor_id'] = str(student.minor_id.id if student.minor_id else '')
    data['majors'] = majors
    data['minors'] = minors
    data['departments'] = departments
    # Handle Undergraduate/Graduate specific data
    if student.student_type == 'Undergraduate':
        undergrad = Undergraduate.objects.filter(student=student).first()
        if undergrad:
            data['undergrad_student_type'] = undergrad.undergrad_student_type
            data['department_id'] = undergrad.department.department_id if undergrad.department else None
            if undergrad.undergrad_student_type == 'FullTime':
                full_time = Undergrad_Full_Time.objects.filter(student=undergrad).first()
                if full_time:
                    data['standing'] = full_time.standing
                    data['creds_earned'] = full_time.creds_earned
            elif undergrad.undergrad_student_type == 'PartTime':
                part_time = Undergrad_Part_Time.objects.filter(student=undergrad).first()
                if part_time:
                    data['standing'] = part_time.standing
                    data['creds_earned'] = part_time.creds_earned
    elif student.student_type == 'Graduate':
        grad = Graduate.objects.filter(student=student).first()
        if grad:
            data['grad_student_type'] = grad.grad_student_type
            data['department_id'] = grad.department.department_id if grad.department else None
            if grad.grad_student_type == 'FullTime':
                full_time = Grad_Full_Time.objects.filter(student=grad).first()
                if full_time:
                    data['year'] = full_time.year
                    data['creds_earned'] = full_time.credits_earned
            elif grad.grad_student_type == 'PartTime':
                part_time = Grad_Part_Time.objects.filter(student=grad).first()
                if part_time:
                    data['year'] = part_time.year
                    data['creds_earned'] = part_time.credits_earned
    print("Data:", data)
    return JsonResponse(data)

@login_required(login_url='user_login')
def update_student_view(request, student_id):
    student = get_object_or_404(Student, studentID=student_id)
    if request.method == 'POST':
        form = StudentEditForm(request.POST, instance=student)
        if form.is_valid():
            form.save()

            # Update/Create Undergraduate/Graduate instances
            student_type = form.cleaned_data['student_type']
            if student_type == 'Undergraduate':
                undergrad, created = Undergraduate.objects.update_or_create(
                    student=student,
                    defaults={'department': form.cleaned_data['department'],
                              'undergrad_student_type': form.cleaned_data['undergrad_student_type']}
                )
                if undergrad.undergrad_student_type == 'FullTime':
                    Undergrad_Full_Time.objects.update_or_create(
                        student=undergrad,
                        defaults={'standing': form.cleaned_data['standing'],
                                  'creds_earned': form.cleaned_data['creds_earned']}
                    )
                    Undergrad_Part_Time.objects.filter(student=undergrad).delete()
                elif undergrad.undergrad_student_type == 'PartTime':
                    Undergrad_Part_Time.objects.update_or_create(
                        student=undergrad,
                        defaults={'standing': form.cleaned_data['standing'],
                                  'creds_earned': form.cleaned_data['creds_earned']}
                    )
                    Undergrad_Full_Time.objects.filter(student=undergrad).delete()
                Graduate.objects.filter(student=student).delete()

            elif student_type == 'Graduate':
                grad, created = Graduate.objects.update_or_create(
                    student=student,
                    defaults={'department': form.cleaned_data['department'],
                              'program': form.cleaned_data['program'],
                              'grad_student_type': form.cleaned_data['grad_student_type']}
                )
                if grad.grad_student_type == 'FullTime':
                    Grad_Full_Time.objects.update_or_create(
                        student=grad,
                        defaults={'year': form.cleaned_data['year'],
                                  'credits_earned': form.cleaned_data['creds_earned'],
                                  'qualifying_exam': form.cleaned_data['qualifying_exam'],
                                  'thesis': form.cleaned_data['thesis']}
                    )
                    Grad_Part_Time.objects.filter(student=grad).delete()
                elif grad.grad_student_type == 'PartTime':
                    Grad_Part_Time.objects.update_or_create(
                        student=grad,
                        defaults={'year': form.cleaned_data['year'],
                                  'credits_earned': form.cleaned_data['creds_earned'],
                                  'qualifying_exam': form.cleaned_data['qualifying_exam'],
                                  'thesis': form.cleaned_data['thesis']}
                    )
                    Grad_Full_Time.objects.filter(student=grad).delete()
                Undergraduate.objects.filter(student=student).delete()

            messages.success(request, "Student updated successfully.")
            return redirect('admin_students_view')
        else:
            messages.error(request, "Error updating student.")
    else:
        form = StudentEditForm(instance=student)

    return JsonResponse({'status': 'error', 'message': f'Method not allowed. {form.errors}'}, status=405)

@login_required(login_url='user_login')
def get_student_grades(request,student_id):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, "You are not authorized to access this resource.")
        return redirect('/homepage/')
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    context['student'] = Student.objects.get(studentID=student_id)
    context['enrollments'] = Enrollment.objects.filter(student=context['student'])
    return render(request, 'admin/admin_student_grades.html', context)


@login_required(login_url='user_login')
def update_gradebook_student(request):
    if request.method == 'POST':
        enrollment_ids = request.POST.getlist('enrollment_id[]')
        grades = request.POST.getlist('grades[]')

        for enrollment_id, grade in zip(enrollment_ids, grades):
            enrollment = get_object_or_404(Enrollment, id=enrollment_id)
            enrollment.grade = grade
            enrollment.save()

        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'error_message': 'Invalid request'}, status=400)

@login_required(login_url='user_login')
def admin_faculty_view(request):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    faculty = Faculty.objects.all()
    for fac in faculty:
        if fac.time_commitment is None or fac.time_commitment == '' or fac.time_commitment == '100%':
            if fac.departments.count() == 1:
                fac.time_commitment = '100%'
            elif fac.departments.count() == 2:
                r = random.randint(0,2)
                if r == 0:
                    fac.time_commitment = '50%/50%'
                elif r == 1:
                    fac.time_commitment = '60%/40%'
                elif r == 2:
                    fac.time_commitment = '30%/70%'
            fac.save()
    context['faculty'] = faculty
    context['departments'] = Department.objects.all()
    return render(request, 'admin/admin_facultys.html', context)

@login_required(login_url='user_login')
def get_faculty_data(request, user_id):
    if not request.user.user.user_type == 'Admin':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized access'}, status=403)
    faculty = get_object_or_404(Faculty, user_id=user_id)
    rank_choices = [{'value': choice[0], 'display': choice[1]} for choice in Faculty.RANK_CHOICES]
    fac_type_choices = [{'value': choice[0], 'display': choice[1]} for choice in Faculty.FAC_TYPE_CHOICES]
    data = {
        'id': faculty.user.id,
        'first_name': faculty.user.first_name,
        'last_name': faculty.user.last_name,
        'email': Login.objects.get(user=faculty.user).email,
        'rank': faculty.rank,
        'fac_type': faculty.fac_type,
        'rank_choices': rank_choices,
        'fac_type_choices': fac_type_choices,
        'specialty': faculty.specialty,
        'department': list(faculty.departments.all().values('department_id')),
        # Additional fields for FullTime/PartTime
        'num_of_courses': faculty.faculty_fulltime.num_of_courses if faculty.fac_type == 'FullTime' else faculty.faculty_parttime.num_of_courses,

    }

    departments = Department.objects.all()
    departments = list(departments.values('department_id', 'department_name'))
    data['departments'] = departments
    try:
        data['office'] = faculty.faculty_fulltime.office.id if faculty.fac_type == 'FullTime' else faculty.faculty_parttime.office.id
    except:
        data['office'] = None
    rooms = Room.objects.all()

    rooms = list(rooms.values('id', 'building__bldg_name', 'room_no'))
    data['rooms'] = rooms
    # print("Data:", data)
    #if failed to get any data, return error
    if not data:
        return JsonResponse({'status': 'error', 'message': 'Failed to get faculty data.'}, status=400)

    return JsonResponse(data)

@login_required(login_url='user_login')
def update_faculty_view(request, user_id):
    faculty = get_object_or_404(Faculty, user_id=user_id)
    if request.method == 'POST':
        form = FacultyEditForm(request.POST, instance=faculty)
        if form.is_valid():
            updated_faculty = form.save()
            if updated_faculty.fac_type == 'FullTime':
                Faculty_PartTime.objects.filter(faculty=updated_faculty).delete()
                Faculty_FullTime.objects.update_or_create(
                    faculty=updated_faculty,
                    defaults={'num_of_courses': form.cleaned_data['num_of_courses'],
                              'office': form.cleaned_data['office']}
                )
            elif updated_faculty.fac_type == 'PartTime':
                Faculty_FullTime.objects.filter(faculty=updated_faculty).delete()
                Faculty_PartTime.objects.update_or_create(
                    faculty=updated_faculty,
                    defaults={'num_of_courses': form.cleaned_data['num_of_courses'],
                              'office': form.cleaned_data['office']}
                )
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = FacultyEditForm(instance=faculty)
    return render(request, 'admin/admin_facultys.html', {'form': form})
@login_required(login_url='user_login')
def admin_college_view(request):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    return render(request, 'admin/admin_college.html', context)
@login_required(login_url='user_login')
def manage_buildings(request):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    buildingForm = BuildingForm()
    context['buildings'] = Building.objects.all()
    context['buildingForm'] = buildingForm
    return render(request, 'admin/college/building.html', context)
@login_required(login_url='user_login')
def add_building(request):
    if request.method == 'POST':
        form = BuildingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Building {form.cleaned_data.get("bldg_name")} added successfully.',extra_tags='Success')
            return redirect('manage_buildings')  # Redirect to building management page
    else:
        form = BuildingForm()
    return render(request, 'admin/college/building.html', {'form': form})
@login_required(login_url='user_login')
def manage_rooms(request, building_id):
    if not request.user.user.user_type == 'Admin':
        messages.error(request, f'You are not authorized to view this page.',extra_tags='Error')
        return redirect('/homepage/')
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    room_form = RoomForm()
    context['building'] = Building.objects.get(pk=building_id)
    context['rooms'] = Room.objects.filter(building=context['building'])
    context['room_form'] = room_form
    return render(request, 'admin/college/room.html', context)
@login_required(login_url='user_login')
def add_room(request, building_id):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            # Add building_id to form
            form.instance.building = Building.objects.get(pk=building_id)
            form.save()
            messages.success(request, f'Room {form.cleaned_data.get("room_no")} added successfully.',extra_tags='Success')
            return redirect('manage_rooms', building_id=building_id)
    return render(request, 'admin/college/room.html', {'form': form})
#endregion

#region statistics

@login_required(login_url='user_login')
def statistics_view(request):
    if not request.user.user.user_type == 'Statistics':
        messages.error(request, f'You are not authorized to view this page.', extra_tags='Error')
        return redirect('/homepage/')
    context = {
        'username': request.user.user.first_name + ' ' + request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    return render(request, 'statistics_view.html', context)
from django.shortcuts import render
from .models import Student, Major, Minor, Department
from django.db.models import Count, Q
@login_required(login_url='user_login')
def college_statistics_view(request):
    if not request.user.user.user_type == 'Statistics':
        messages.error(request, f'You are not authorized to view this page.', extra_tags='Error')
        return redirect('/homepage/')
    # Undergraduates vs Graduates
    # Pie chart data
    undergrad_count = Student.objects.filter(student_type='Undergraduate').count()
    grad_count = Student.objects.filter(student_type='Graduate').count()
    fulltime_count = Student.objects.filter(undergraduate__undergrad_student_type='FullTime').count() + Student.objects.filter(graduate__grad_student_type='FullTime').count()
    parttime_count = Student.objects.filter(undergraduate__undergrad_student_type='PartTime').count() + Student.objects.filter(graduate__grad_student_type='PartTime').count()

    # Bar chart data
    major_counts = Major.objects.annotate(student_count=Count('student')).values('major_name', 'student_count')
    minor_counts = Minor.objects.annotate(student_count=Count('student')).values('minor_name', 'student_count')
    grad_department_counts = Department.objects.annotate(grad_count=Count('graduate')).values('department_name', 'grad_count')

    context = {
        'username': request.user.user.first_name + ' ' + request.user.user.last_name,
        'usertype': request.user.user.user_type,
        'undergrad_count': undergrad_count,
        'grad_count': grad_count,
        'fulltime_count': fulltime_count,
        'parttime_count': parttime_count,
        'major_counts': list(major_counts),
        'minor_counts': list(minor_counts),
        'grad_department_counts': list(grad_department_counts),
    }
    return render(request, 'statistics/enrollment.html', context)
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
def search_student_view(request):
    if request.method == 'POST':
        student_id = request.POST.get('studentID')
        try:
            student = Student.objects.get(studentID=student_id)
            student_history = StudentHistory.objects.filter(student=student)
            history_data = []
            for history in student_history:
                course = CourseSection.objects.get(crn=history.section.crn).course.course_name
                history_data.append({'course': course, 'grade': history.grade, 'semester': history.semester.semester_name})

            return JsonResponse({'status': 'success', 'history': history_data, 'student': {'first_name': student.user.first_name, 'last_name': student.user.last_name, 'studentID': student.studentID}})
        except Student.DoesNotExist:
            print("Student not found")
            return JsonResponse({'status': 'error', 'message': 'Student not found'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

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
    #if date is before semester end date, pass disabled = true to template
    if (datetime.date.today() < (section.semester.end_date - datetime.timedelta(days=5))) or (datetime.date.today() > (section.semester.end_date + datetime.timedelta(days=14))):
        context['disabled'] = True

    context['enrollments'] = StudentHistory.objects.filter(section=section)
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

    enrollments = StudentHistory.objects.filter(section=section)
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
    enrollments = StudentHistory.objects.filter(section=section)
    attendances = {}
    previous_attendances = Attendance.objects.filter(section=section)
    #get dates of previous attendances
    dates = []
    for attendance in previous_attendances:
        if attendance.date_of_class not in dates:
            dates.append(attendance.date_of_class)
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
        'selected_date': request.POST.get('date_of_class', datetime.date.today().strftime("%Y-%m-%d")),  # Default to today's date
        'previous_dates': dates,
        'has_previous_dates': len(dates) > 0,
    }
    #set current datetime timezone to -5 hours to match timezone
    current_time = datetime.datetime.now() - datetime.timedelta(hours=5)
    current_time = datetime.time(current_time.hour, current_time.minute, current_time.second)
    #if current time is outside of class time up to an hour later, pass disabled = true to template
    print("Current Time:", current_time)
    #start_time and end_time come from timeslot.periods, a many to many field
    start_time = section.timeslot.periods.all()[0].start_time
    start_time = datetime.time(start_time.hour, start_time.minute, start_time.second)
    print("Start Time:", start_time)
    end_time = section.timeslot.periods.all()[0].end_time
    end_time = datetime.time(end_time.hour, end_time.minute, end_time.second)
    print("End Time:", end_time)
    #if current time is outside of class time, or if date is not today, pass disabled = true to template
    #if section.timeslot.day is not today (Monday, Tuesday, etc), pass disabled = true to template
    if (current_time < start_time or current_time > end_time) or \
        (date != datetime.date.today()) or (date is None) or \
        not any(day.weekday == datetime.date.today().strftime('%A') for day in section.timeslot.days.all()):
        context['disabled'] = True
    else:
        context['disabled'] = False
    if date is None:
        date = (datetime.datetime.now().date() - datetime.timedelta(hours=5))
    context['reason'] = []
    if (current_time < start_time or current_time > (end_time)):
        context['reason'].append('Current time is outside of class time.')
    if (date != datetime.datetime.now().date()):
        context['reason'].append('Date is not today.')
    today_weekday = datetime.date.today().strftime("%A")
    if all(day.weekday != today_weekday for day in section.timeslot.days.all()):
        context['reason'].append('Class is not held on this day: ' + today_weekday + '.')
    # if date is earlier than semester.start_date or later than semester.end_date, pass disabled = true to template
    semester = section.semester

    if date < semester.start_date or date > semester.end_date:
        context['disabled'] = True
        context['reason'].append('Date is not within the semester.')
    context['start_date'] = start_time
    context['end_date'] = end_time
    context['current_date'] = current_time
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
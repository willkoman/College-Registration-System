import datetime
from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse

from .forms import UserCompositeForm
from .models import CoursePrereq, Semester,Hold, CourseSection,Department, Course,Login,Enrollment,Day,StudentHistory, User, Admin, Student, Faculty,Faculty_FullTime, Faculty_PartTime, Graduate, Undergraduate, Major
from django.contrib import messages
import requests
import json


add_drop_periods = Semester.objects.all().order_by('start_date')
#add_drop periods end 2 weeks after the start date of the semester and start 4 weeks before the start date of the semester
for period in add_drop_periods:
    period.add_drop_end_date = period.start_date + datetime.timedelta(days=14)
    period.add_drop_start_date = period.start_date - datetime.timedelta(days=28)
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
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if email and password:  # Check if email and password are not Nonew
            userlogin = authenticate(request, email=email, password=password)
        else:
            error_message = "Email and/or Password cannot be blank."
        print("Userlogin:", userlogin)  # Debugging line

        if userlogin is not None:
            login(request, userlogin)
            try:
                print("User Type:", userlogin.user.user_type)  # Debugging line
                if userlogin.user.user_type == 'Admin':
                    # return redirect('/admin/')
                    pass
                elif userlogin.user.user_type in ['Faculty', 'Student']:
                    if userlogin.is_locked:
                        error_message = "Your account is locked. Please contact the system administrator."
                        return render(request, 'login.html',{'error_message': error_message})
                userlogin.no_of_attempts = 0  # Reset the no_of_attempts to 0
                userlogin.save()  # Save the updated Login object
                return redirect('/homepage/')
            except Exception as e:
                print("Exception:", e)  # Debugging line
                error_message="Error: User type not recognized."
        else:
            try:
                login_obj = Login.objects.get(email=email)  # Get the Login object based on the email
                if login_obj.no_of_attempts >= 3:
                    error_message = "You have exceeded the maximum number of login attempts. Please contact the system administrator."
                    login_obj.is_locked = True  # Lock the Login object
                    login_obj.save()  # Save the updated Login object
                    return render(request, 'login.html',{'error_message': error_message})
                login_obj.no_of_attempts += 1  # Increment the no_of_attempts by 1
                login_obj.save()  # Save the updated Login object
            except Login.DoesNotExist:
                # Handle the case where the email does not exist in the Login table
                pass
            error_message="Invalid login credentials."
    return render(request, 'login.html',{'error_message': error_message})

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
        })

        context['departments'] = Department.objects.all()
        #context['timeslots'] = Timeslot.objects.all()
        context['semesters'] = Semester.objects.all()

    context['sections']=formatted_sections
    return render(request, 'schedule.html', context)
#endregion
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
    return render(request, 'faculty_view.html', context)


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
            raise Exception("You have already registered for a course in this timeslot.")
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
        # semes = section.semester
        # semes = add_drop_periods[0] if semes == add_drop_periods[0] else add_drop_periods[1]
        # if datetime.date.today() < semes.add_drop_start_date or datetime.date.today() > semes.add_drop_end_date:
        #     raise Exception(f"Add/Drop period for {section.semester} has ended. The period is {semes.add_drop_start_date} - {semes.add_drop_end_date}")

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


#### ADMIN VIEWS ####
@login_required(login_url='user_login')
def admin_users_view(request, user_id=None):
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
    user_id = request.GET.get('user_id')
    user = User.objects.get(id=user_id)
    form = UserCompositeForm(instance=user)

    # Assuming you're using Django templates, render the form to a template,
    # or find another way to split the form fields based on user type.
    return render(request, 'partials/edituser.html', {'form': form})

def update_user(request):
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
def admin_course_view(request):
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    context['courses'] = Course.objects.all()
    return render(request, 'admin/admin_courses.html', context)
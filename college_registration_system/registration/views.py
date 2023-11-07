import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from .models import CoursePrereq, CourseSection,Department, Course,Login,Enrollment,Day,StudentHistory, User, Admin, Student, Faculty,Faculty_FullTime, Faculty_PartTime, Graduate, Undergraduate, Major
from django.contrib import messages

@login_required
def root_redirect(request):
    #if login that has that user is superuser, redirect to admin page
    if request.user.is_superuser:
        return redirect('/admin/')
    else:
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
                    return redirect('/admin/')
                elif userlogin.user.user_type in ['Faculty', 'Student']:
                    if userlogin.is_locked:
                        error_message = "Your account is locked. Please contact the system administrator."
                        return render(request, 'login.html',{'error_message': error_message})
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

def homepage(request):
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


    elif request.user.user.user_type == 'Faculty':
        #get faculty with that user and append to context
        context['faculty'] = Faculty.objects.get(user=user)
        try:
            context['office'] = Faculty_FullTime.objects.get(faculty=context['faculty']).office
        except:
            context['office'] = Faculty_PartTime.objects.get(faculty=context['faculty']).office

        print("Faculty:", context['faculty'])
    return render(request, 'homepage.html', context)

def logout_view(request):
    logout(request)
    return redirect('/login/')

def schedule_view(request):
    user = request.user.user
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
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

    context['sections']=formatted_sections
    return render(request, 'schedule.html', context)

def registered_sessions_view(request):
    student = request.user.student  # Assuming you have a ForeignKey from User to Student
    registered_sessions = Enrollment.objects.filter(student=student)
    return render(request, 'registered_sessions.html', {'registered_sessions': registered_sessions})

def course_history_view(request):
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    student = Student.objects.get(user=request.user.user)
    context['course_history'] = StudentHistory.objects.filter(student=student)
    return render(request, 'course_history.html',context)

def student_view(request):
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

def enrollment_view(request):
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

def register(request, section_id):
    #distionary assigning number to grade
    grade_dict = {'A':4,'B':3,'C':2,'D':1,'F':0,'NA':0}
    try:
        student = request.user.user.student
        section = CourseSection.objects.get(crn=section_id)
        enrollment = Enrollment(student=student, section=section, date_of_enrollment=datetime.date.today(), grade='NA')
        # if enrollment already exists with the student and same section, raise an exception
        if Enrollment.objects.filter(student=student, section=section).exists():
            raise Exception("You have already registered for this section.")
        if Enrollment.objects.filter(student=student).count() >= 4:
            raise Exception("You have already registered for 4 courses in this semester.")
        #if same timeslot in coursesection already in enrollment, raise exception
        if Enrollment.objects.filter(student=student, section__timeslot=section.timeslot).exists():
            raise Exception("You have already registered for a course in this timeslot.")
        if CoursePrereq.objects.filter(course=section.course).exists():
            prereqs = CoursePrereq.objects.filter(course=section.course)
            for prereq in prereqs:
                if not StudentHistory.objects.filter(student=student, section__course=prereq.pr_course).exists():
                    raise Exception(f"You have not completed the prerequisite course: {prereq.pr_course}")
                elif grade_dict[StudentHistory.objects.get(student=student, section__course=prereq.pr_course).grade] < grade_dict[prereq.min_grade]:
                    raise Exception(f"You have not achieved a high enough grade for: {prereq.pr_course}")

        enrollment.save()
        # Add a success message
        messages.success(request, f'You have successfully registered for {section}!',extra_tags='Success')
    except Exception as e:
        print("Exception:", e)
        # Add a failure message
        messages.error(request, f'An error occurred while registering for {section}.\n{e}',extra_tags='Error')
    return redirect('/schedule/')

def drop_course(request,section_id):
    try:
        student = request.user.user.student
        section = CourseSection.objects.get(crn=section_id)
        enrollment = Enrollment.objects.get(student=student, section=section)
        enrollment.delete()
        # Add a success message
        messages.success(request, f'You have successfully dropped {section}!',extra_tags='Success')
    except Exception as e:
        print("Exception:", e)
        # Add a failure message
        messages.error(request, f'An error occurred while dropping {section}.\n{e}',extra_tags='Error')
    return redirect('/enrollment/')

def course_view(request,course_id):
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    course = Course.objects.get(course_id=course_id)
    context['course'] = course
    prereqs = CoursePrereq.objects.filter(course=course)
    context['prereqs'] = prereqs
    return render(request, 'course.html', context)

def faculty_directory(request):
    # Retrieve all Faculty objects and their related Faculty_FullTime and Faculty_PartTime objects
    faculty = Faculty.objects.select_related('faculty_fulltime', 'faculty_parttime')

    context = {
        'username': request.user.user.first_name + ' ' + request.user.user.last_name,
        'usertype': request.user.user.user_type,
        'faculty': faculty,
    }
    return render(request, 'faculty_directory.html', context)

def department_directory(request):
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    context['departments'] = Department.objects.all()
    return render(request, 'department_directory.html', context)

def major_directory(request):
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    context['majors'] = Major.objects.all().distinct()
    return render(request, 'major_directory.html', context)

def faculty_view(request,user_id):
    context = {
        'username': request.user.user.first_name+' '+request.user.user.last_name,
        'usertype': request.user.user.user_type,
    }
    faculty = Faculty.objects.get(user=user_id)
    context['faculty'] = faculty
    try:
        context['office'] = Faculty_FullTime.objects.get(faculty=faculty).office
    except:
        context['office'] = Faculty_PartTime.objects.get(faculty=faculty).office
    return render(request, 'faculty.html', context)
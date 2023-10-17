from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from .models import CourseSection, Login, User, Admin, Student, Faculty,Faculty_FullTime, Faculty_PartTime, Graduate, Undergraduate

@login_required
def root_redirect(request):
    if request.user.user.user_type=='Admin':  # Assuming you have a field to identify superusers
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
    course_sections = CourseSection.objects.all()
    formatted_sections = []

    for section in course_sections:
        timeslot = section.timeslot  # Assuming you have a ForeignKey to Timeslot in CourseSection
        days_str = ', '.join([str(day) for day in timeslot.days.all()])
        periods_str = ', '.join([f"{period.start_time} - {period.end_time}" for period in timeslot.periods.all()])

        formatted_sections.append({
            'crn': section.crn,
            'course': section.course.course_name,
            'section': section.crn,
            'timeslot': periods_str,
            'department' : section.course.department,
            'credits': section.course.no_of_credits,
            'days': days_str,
            'room': str(section.room.building)+str(section.room.room_no),
            'faculty': section.faculty,
        })

    context = {'sections': formatted_sections}
    return render(request, 'schedule.html', context)


from django import forms
from .models import Course, Major, Minor, User, Login, Student, Faculty, Admin, Department, CourseSection, Undergraduate,Graduate,Grad_Full_Time,Grad_Part_Time,Undergrad_Full_Time,Undergrad_Part_Time
from django.contrib.admin.forms import AdminAuthenticationForm

class LoginForm(forms.ModelForm):
    class Meta:
        model = Login
        fields = ['email', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

class CustomAdminAuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.user.user_type == 'Admin':  # Replace with your actual field and value
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name},
            )
class UserCompositeForm(forms.ModelForm):
    # Login model fields
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    no_of_attempts = forms.IntegerField()
    is_locked = forms.BooleanField(required=False, initial=False)
    # Student model fields
    studentID = forms.CharField(required=False)
    major_id = forms.ModelChoiceField(queryset=Major.objects.all(), required=False)
    minor_id = forms.ModelChoiceField(queryset=Minor.objects.all(), required=False)
    enrollment_year = forms.IntegerField(required=False)
    student_type = forms.ChoiceField(choices=Student.STUDENT_TYPE_CHOICES, required=False)
    # Faculty model fields
    rank = forms.ChoiceField(choices=Faculty.RANK_CHOICES, required=False)
    departments = forms.ModelMultipleChoiceField(queryset=Department.objects.all(), required=False)
    specialty = forms.CharField(max_length=50, required=False)
    fac_type = forms.ChoiceField(choices=Faculty.FAC_TYPE_CHOICES, required=False)
    # Admin model fields
    access_level = forms.ChoiceField(choices=Admin.ACCESS_LEVEL_CHOICES, required=False)
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'gender', 'dob', 'street', 'city', 'state', 'zip_code', 'user_type']

    def __init__(self, *args, **kwargs):
        super(UserCompositeForm, self).__init__(*args, **kwargs)
        user = kwargs.get('instance')

        # Initialize form fields
        if user:
            if hasattr(user, 'login'):
                self.fields['email'].initial = user.login.email
                self.fields['no_of_attempts'].initial = user.login.no_of_attempts
                self.fields['is_locked'].initial = user.login.is_locked
            if hasattr(user, 'student'):
                self.fields['studentID'].initial = user.student.studentID
                self.fields['major_id'].initial = user.student.major_id
                self.fields['minor_id'].initial = user.student.minor_id
                self.fields['enrollment_year'].initial = user.student.enrollment_year
                self.fields['student_type'].initial = user.student.student_type
            if hasattr(user, 'faculty'):
                self.fields['rank'].initial = user.faculty.rank
                self.fields['departments'].initial = user.faculty.departments
                self.fields['specialty'].initial = user.faculty.specialty
                self.fields['fac_type'].initial = user.faculty.fac_type
            if hasattr(user, 'admin'):
                self.fields['access_level'].initial = user.admin.access_level
            # Initialize Faculty and Admin fields similarly

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            user.login.set_password(password)  # Hash the password

        if commit:
            user.save()
            if hasattr(user, 'login'):
                login_instance = user.login
                login_instance.email = self.cleaned_data.get('email')
                login_instance.no_of_attempts = self.cleaned_data.get('no_of_attempts')
                login_instance.is_locked = self.cleaned_data.get('is_locked')

                # Handle password separately
                password = self.cleaned_data.get('password')
                if password:
                    login_instance.set_password(password)

                login_instance.save()

            # Handle saving other related objects (Student, Faculty, Admin)

            # ...

        return user

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        exclude = ['course_id']
        fields = ['course_name','course_number', 'department', 'no_of_credits', 'description', 'course_type']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class CourseSectionForm(forms.ModelForm):
    class Meta:
        model = CourseSection
        exclude = ['crn','course']
        fields = ['faculty', 'timeslot', 'room', 'semester', 'available_seats']
        widgets = {
            'timeslot': forms.Select(attrs={'class': 'form-control'}),
            'room': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'faculty': forms.Select(attrs={'class': 'form-control'}),
            'available_seats': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class StudentEditForm(forms.ModelForm):
    # Additional fields for subtypes
    undergrad_student_type = forms.ChoiceField(choices=Undergraduate.UNDERGRAD_STUDENT_TYPE_CHOICES, required=False)
    grad_student_type = forms.ChoiceField(choices=Graduate.GRAD_STUDENT_TYPE_CHOICES, required=False)
    standing = forms.ChoiceField(choices=Undergrad_Full_Time.STANDING_CHOICES, required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    # min_creds = forms.IntegerField(required=False)
    # max_creds = forms.IntegerField(required=False)
    creds_earned = forms.IntegerField(required=False)
    year = forms.IntegerField(required=False)
    qualifying_exam = forms.BooleanField(required=False)
    thesis = forms.BooleanField(required=False)

    class Meta:
        model = Student
        fields = ['major_id', 'minor_id', 'enrollment_year', 'student_type', 'department']
        widgets = {
            'major_id': forms.Select(attrs={'class': 'form-control'}),
            'minor_id': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'enrollment_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'student_type': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super(StudentEditForm, self).__init__(*args, **kwargs)
        # Initialize the subtype fields if the instance is provided
        if self.instance.pk:
            if hasattr(self.instance, 'undergraduate'):
                undergrad = self.instance.undergraduate
                self.fields['undergrad_student_type'].initial = undergrad.undergrad_student_type
                self.fields['department'].initial = undergrad.department
                if undergrad.undergrad_student_type == 'FullTime':
                    full_time = undergrad.undergrad_full_time
                    self.fields['standing'].initial = full_time.standing
                    # self.fields['min_creds'].initial = full_time.min_creds
                    # self.fields['max_creds'].initial = full_time.max_creds
                    self.fields['creds_earned'].initial = full_time.creds_earned
                elif undergrad.undergrad_student_type == 'PartTime':
                    part_time = undergrad.undergrad_part_time
                    self.fields['standing'].initial = part_time.standing
                    # self.fields['min_creds'].initial = part_time.min_creds
                    # self.fields['max_creds'].initial = part_time.max_creds
                    self.fields['creds_earned'].initial = part_time.creds_earned
            if hasattr(self.instance, 'graduate'):
                graduate = self.instance.graduate
                self.fields['grad_student_type'].initial = graduate.grad_student_type
                self.fields['department'].initial = graduate.department
                if graduate.grad_student_type == 'FullTime':
                    full_time = graduate.grad_full_time
                    self.fields['year'].initial = full_time.year
                    self.fields['qualifying_exam'].initial = full_time.qualifying_exam
                    self.fields['thesis'].initial = full_time.thesis
                elif graduate.grad_student_type == 'PartTime':
                    part_time = graduate.grad_part_time
                    self.fields['year'].initial = part_time.year
                    self.fields['qualifying_exam'].initial = part_time.qualifying_exam
                    self.fields['thesis'].initial = part_time.thesis
    def save(self, commit=True):
        student = super().save(commit=False)

        # Handle other student fields...

        if commit:
            student.save()

            # Handling the department for Undergraduate or Graduate
            if self.cleaned_data['student_type'] == 'Undergraduate':
                undergrad, created = Undergraduate.objects.get_or_create(student=student)
                undergrad.department = self.cleaned_data['department']
                undergrad.save()

            elif self.cleaned_data['student_type'] == 'Graduate':
                grad, created = Graduate.objects.get_or_create(student=student)
                grad.department = self.cleaned_data['department']
                grad.save()
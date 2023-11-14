from django import forms
from .models import Major, Minor, User, Login, Student, Faculty, Admin, Department
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
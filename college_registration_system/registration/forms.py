from django import forms
from .models import Login
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

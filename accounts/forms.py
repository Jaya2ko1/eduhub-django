from django import forms
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name','password1','password2',]

    def clean_username(self):
        username = self.cleaned_data['username']

        if len(username) <3:
            raise forms.ValidationError(
            "Username must be at least 3 characters."
            )
        if len(username) > 20:
            raise forms.ValidationError(
                "Username cannot exceed 20 characters."
                )

        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        filter_mail = User.objects.filter(email=email)

        if filter_mail.exists():
            raise forms.ValidationError(
                        "this Email is already registered.")
        return email

class CustomLoginForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control','placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control','placeholder': 'Password'}))

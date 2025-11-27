from django import forms
from .users_models import User

class login_form(forms.Form):
    username = forms.CharField(label='User name', max_length=150)
    password = forms.CharField(label='Password', max_length=255)

class register_form(forms.Form):
    username = forms.CharField(label='User name', max_length=150)
    password = forms.CharField(label='Password', max_length=255)
    fullname = forms.CharField(label='Full name',max_length=150)
    email = forms.CharField(max_length=255)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Tên đăng nhập này đã được sử dụng.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Địa chỉ Email này đã được đăng ký.")
        return email
from django import forms


# Only two fields are going to be translated
class LoginForm(forms.Form):
    username = forms.CharField(max_length=256)
    password = forms.CharField(widget=forms.PasswordInput(), max_length=256)


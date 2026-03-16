from django import forms
from django.core.exceptions import ValidationError


class PasswordChangeForm(forms.Form):
    username = forms.CharField(
        label="用户名",
        widget=forms.TextInput(attrs={"class": "form-control form-control-lg border-left-0"}),
        required=True
    )
    current_password = forms.CharField(
        label="当前密码",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg border-left-0"}),
        required=True
    )
    new_password = forms.CharField(
        label="新密码",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg border-left-0"}),
        required=True,
        min_length=6
    )
    confirm_password = forms.CharField(
        label="确认新密码",
        widget=forms.PasswordInput(attrs={"class": "form-control form-control-lg border-left-0"}),
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError("两次输入的密码不一致！")

        return cleaned_data


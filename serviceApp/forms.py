from django import forms
from django.contrib.auth.models import User
from loginApp.models import Customer

class EditProfileForm(forms.ModelForm):
    birthdate = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}), 
        required=False
    )

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email', 'phone', 'birth_date']
        labels = {
            'name': 'ชื่อ',
            'email': 'อีเมล',
            'phone': 'เบอร์โทรศัพท์',
            'birthdate': 'วันเกิด',
        }

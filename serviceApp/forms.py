from django import forms
from django.contrib.auth.models import User
from loginApp.models import Customer
from .models import Staff,Review,Booking

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

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['name', 'speciality', 'role', 'commission_rate', 'phone', 'birthdate', 'status']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comments']

    review_date = forms.DateField(widget=forms.SelectDateWidget(years=range(2000, 2100)))

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['customer', 'booking_date', 'service', 'staff']

    booking_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        self.fields['customer'].widget.attrs.update({'class': 'form-control'})
        self.fields['service'].widget.attrs.update({'class': 'form-select'})
        self.fields['staff'].widget.attrs.update({'class': 'form-select'})

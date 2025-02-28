from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from datetime import datetime
from .form import StaffForm
from .models import Booking,Staff,Service,Payment
import json

@login_required(login_url='/login')
def account(request):
    user = request.user
    customer = getattr(user, 'customer', None)

    context = {
        "name": user.get_full_name(),
        "email": user.email,
        "address": customer.address if hasattr(customer, 'address') else '',
        "phone": customer.phone if hasattr(customer, 'phone') else '',
        "birthdate": str(customer.birthdate) if hasattr(customer, 'birthdate') else ''
    }

    return render(request, 'account.html', context)

@login_required
def payment_methods(request):
    user = request.user
    customer = getattr(user, 'customer', None)

    if not customer:
        return JsonResponse({'error': 'Customer profile not found'}, status=404)

    payments = Payment.objects.filter(booking__customer_id=customer).values(
        'payment_id', 'amount', 'payment_date', 'payment_method', 'status'
    )

    return JsonResponse(list(payments), safe=False)


@login_required
def user_data(request):
    user = request.user
    customer = getattr(user, 'customer', None)  # Ensure user has a Customer profile

    if not customer:
        return JsonResponse({'error': 'Customer profile not found'}, status=404)

    return JsonResponse({
        "name": user.get_full_name(),
        "email": user.email,
        "address": customer.address if hasattr(customer, 'address') else '',
        "phone": customer.phone if hasattr(customer, 'phone') else '',
        "birthdate": str(customer.birthdate) if hasattr(customer, 'birthdate') else '',
    })

def booking_history(request):
    user = request.user
    customer = getattr(user, 'customer', None)

    if not customer:
        return JsonResponse({'error': 'Customer profile not found'}, status=404)

    bookings = Booking.objects.filter(customer_id=customer).values(
        'booking_id', 'booking_date', 'service__name', 'status'
    )

    return JsonResponse(list(bookings), safe=False)


def booking_view(request):

    staff_list = Staff.objects.all()
    service_list = Service.objects.all()

    return render(request, 'booking1.html', {
        'staff_list': staff_list,
        'service_list': service_list,
    })

@csrf_exempt
def save_booking(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            booking_date = datetime.strptime(data['date'], '%Y-%m-%d').date()

            staff = Staff.objects.get(staff_id=data['staff']) 
            service = Service.objects.get(service_id=data['service'])  

            # ตรวจสอบว่าเป็นผู้ใช้ที่ล็อกอินอยู่หรือไม่
            if request.user.is_authenticated:
                customer = request.user.id
            else:
                customer = None  # ถ้าไม่ได้ล็อกอิน

            # ถ้าไม่มี customer ให้ใช้ temp_customer จากข้อมูลใน data
            temp_customer = None
            if data.get('tempCustomer'):
                temp_customer = TemporaryCustomer.objects.get(id=data['tempCustomer'])
            
            # ถ้าไม่มี customer และไม่มี temp_customer ให้ส่งข้อผิดพลาด
            if not customer and not temp_customer:
                return JsonResponse({"status": "error", "message": "No valid customer or temp_customer found."}, status=400)

            # สร้าง booking
            booking = Booking.objects.create(
                staff=staff, 
                service=service,  
                customer_id=customer,
                booking_date=booking_date,
                status='Pending', 
                walk_in=data.get('walkIn', False),  
                commission_amount=data.get('commissionAmount', 0.00),  
                temp_customer=temp_customer,  
            )

            # สร้าง payment ถ้ามี
            if data.get('paymentMethod'):
                amount = data.get('amount', 0.00)  
                payment = Payment.objects.create(
                    staff=staff,
                    payment_date=datetime.now(),
                    amount=amount,  
                    payment_method=data['paymentMethod'],
                    status='Pending',  
                    note=data.get('additionalNotes', ''),
                )
                booking.payment = payment
                booking.save()

            return JsonResponse({"status": "success", "message": "Booking saved!", "booking_id": booking.booking_id})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

def admin_bookings(request):
    bookings = Booking.objects.all()
    return render(request, 'admin-bookings.html', {'bookings': bookings})

def manage_staff(request):
    if request.method == "POST":
        form = StaffForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin-users.html')
    else:
        form = StaffForm()
    staff_list = Staff.objects.all()
    return render(request, 'admin-users.html', {'form': form, 'staff_list': staff_list})


# Create your views here.
def service(request):
    return render(request,'service.html')

def review(request):
    return render(request,'review.html')

@login_required(login_url='login')
def booking1(request):
    return render(request,'booking1.html')

@login_required(login_url='/login')
def account(request):
    return render(request,'account.html')

def a_dashboard(request):
    return render(request,'ad.html')

def a_emp(request):
    return render(request,'admin-employees.html')

def a_playment(request):
    return render(request,'admin-payments.html')

def a_review(request):
    return render(request,'admin-reviews.html')

def a_service(request):
    return render(request,'admin-services.html')

def a_users(request):
    return render(request,'admin-users.html')
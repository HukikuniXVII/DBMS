from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect ,get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import datetime
from .forms import EditProfileForm,StaffForm,ReviewForm
from .models import Booking,Staff,Service,Payment,Review
from loginApp.models import Customer
from django.contrib import messages
from django.db.models import Avg
import json
from django.db import transaction


def admin_payments(request):
    payments = Payment.objects.all()
    return render(request, 'admin-payments.html', {'payments': payments})

def manage_reviews(request):
    reviews_list = Review.objects.all()
    return render(request, 'admin-reviews.html', {'reviews_list': reviews_list})

def service_list(request):
    services = Service.objects.all()
    return render(request, 'service.html', {'services': services})

@csrf_exempt
def get_reviews(request):
    if request.method == "GET":
        reviews = Review.objects.select_related("user").order_by("-review_date")[:10] 
        review_list = [
            {
                "name": review.user.get_full_name(),
                "date": review.review_date.strftime("%d %B %Y"),
                "rating": review.rating,
                "comment": review.comments,
                "profile_img": "https://img.freepik.com/premium-vector/portrait-beautiful-women-round-frame-avatar-female-character-isolated-white-background_559729-210.jpg?w=740"
            }
            for review in reviews
        ]
        return JsonResponse({"reviews": review_list}, safe=False)
    return JsonResponse({"error": "Invalid request method"}, status=405)

def get_review_stats(request):
    reviews = Review.objects.all()
    total_reviews = reviews.count()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    rating_counts = {i: reviews.filter(rating=i).count() for i in range(1, 6)}

    return JsonResponse({
        "total_reviews": total_reviews,
        "avg_rating": round(avg_rating, 1),
        "rating_counts": rating_counts,
    })

@csrf_exempt
def submit_review(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            rating = int(data.get("rating",0))
            comments = data.get("comments", "")

            # ตรวจสอบว่า rating อยู่ในช่วงที่ถูกต้อง (1-5)
            if not (1 <= rating <= 5):
                return JsonResponse({"error": "Invalid rating"}, status=400)

            # บันทึกรีวิวลง Database
            Review.objects.create(
                user=request.user, 
                rating=rating,
                comments=comments,
                review_date=datetime.date.today()
            )
        
            return JsonResponse({"message": "Review submitted successfully"})
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def delete_user(request, user_id):
    user = get_object_or_404(Customer, id=user_id)

    if request.method == 'POST':
        user.delete()
        return redirect('admin_users')

    return render(request, 'admin-users.html', {'user': user})

def edit_profile(request, user_id):
    user = get_object_or_404(Customer, id=user_id)

    if request.method == "POST":
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.phone = request.POST.get("phone") 
        user.birth_date = request.POST.get("birth_date") 
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("account") 

    return render(request, "account", {"user": user})

@login_required
def account_view(request):
    user = request.user
    try:
        customer = Customer.objects.get(email=user.email)
    except Customer.DoesNotExist:
        customer = None

    bookings = Booking.objects.filter(customer=customer).select_related('service', 'staff', 'slot').order_by('-booking_date')

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=user)
        if form.is_valid() and customer:
            customer.first_name = form.cleaned_data['first_name']
            customer.last_name = form.cleaned_data['last_name']
            customer.email = form.cleaned_data['email']
            customer.phone = form.cleaned_data['phone']
            customer.birth_date = form.cleaned_data['birthdate']
            customer.save()
            return redirect('account')
    else:
        form = EditProfileForm(initial={
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'email': customer.email,
            'phone': customer.phone,
            'birth_date': customer.birth_date,
        })

    return render(request, 'account.html', {'user': user, 'customer': customer, 'bookings': bookings, 'form': form})

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

            booking_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()

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
                start_time=data['startTime'],  # เพิ่ม start_time
                end_time=data['endTime'],  # เพิ่ม end_time ที่คำนวณแล้ว
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

def get_service_duration(request, service_id):
    try:
    
        service = Service.objects.get(service_id=service_id)

        return JsonResponse({'duration': service.duration})
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)


def admin_bookings(request):
    bookings = Booking.objects.all().select_related('customer', 'service', 'staff').values(
        'service_id', 'customer__email', 'booking_date', 'service__name', 'staff__name', 'status','booking_id'
    )
    return render(request, 'admin-bookings.html', {'bookings': list(bookings)})

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

def review(request):
    return render(request,'review.html')

@login_required(login_url='login')
def booking1(request):
    return render(request,'booking1.html')

@login_required(login_url='/login')
def account(request):
    return render(request,'account.html')

def edit_staff(request, staff_id):
    staff = get_object_or_404(Staff, pk=staff_id)

    if request.method == 'POST':
        staff.name = request.POST.get('name')
        staff.speciality = request.POST.get('speciality')
        staff.role = request.POST.get('role')
        staff.commission_rate = request.POST.get('commission_rate')
        staff.phone = request.POST.get('phone')
        staff.birthdate = request.POST.get('birthdate')
        staff.status = request.POST.get('status')

        staff.save()
        return redirect('manage_staffs')

    return render(request, 'edit_staff.html', {'staff': staff})

def delete_staff(request, staff_id):
    staff = get_object_or_404(Staff, pk=staff_id)
    staff.delete()
    return redirect('manage_staffs')

def manage_services(request):
    service_list = Service.objects.all()
    return render(request, 'admin-services.html', {'service_list': service_list})

def edit_service(request):
    if request.method == 'POST':
        service_id = request.POST.get('service_id')
        service = get_object_or_404(Service, service_id=service_id)
        service.name = request.POST.get('name')
        service.description = request.POST.get('description')
        service.duration = request.POST.get('duration')
        service.price = request.POST.get('price')
        service.save()
        return redirect('admin-services')

def delete_service(request, service_id):
    service = get_object_or_404(Service, service_id=service_id)
    service.delete()
    return redirect('admin-services')

def add_service(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        duration = request.POST.get('duration_end')
        price = request.POST.get('price')

        Service.objects.create(name=name, description=description, duration=duration, price=price)
        return redirect('admin-services') 

    return render(request, 'admin-services.html')

def manage_staffs(request):
    staff_list = Staff.objects.all()
    return render(request, 'admin-employees.html', {'staff_list': staff_list})

def add_staff(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        speciality = request.POST.get('speciality')
        role = request.POST.get('role')
        commission_rate = request.POST.get('commission_rate')
        phone = request.POST.get('phone')
        birthdate = request.POST.get('birthdate')
        status = request.POST.get('status', "Available")

        Staff.objects.create(
            name=name,
            speciality=speciality,
            role=role,
            commission_rate=commission_rate,
            phone=phone,
            birthdate=birthdate if birthdate else "1970-01-01",
            status=status
        )
        return redirect('admin-employees') 

    return render(request, 'admin-employees.html')

def admin_users_view(request):
    customers = Customer.objects.all()
    return render(request, 'admin-users.html', {'customer': customers})

def update_booking_status(request, booking_id, status):
    booking = get_object_or_404(Booking, booking_id=booking_id)

    if status not in ['Pending', 'Paid', 'Confirmed', 'Canceled']:
        return JsonResponse({'success': False, 'error': 'Invalid booking status'}, status=400)
    
    booking.status = status
    booking.save()

    if status in ['Paid', 'Confirmed']:
        with transaction.atomic():
            payments = Payment.objects.filter(booking=booking)
            for payment in payments:
                payment.status = 'Paid'
                payment.save()
    
    if status in ['Canceled']:
        with transaction.atomic():
            payments = Payment.objects.filter(booking=booking)
            for payment in payments:
                payment.status = 'Canceled'
                payment.save()

    return JsonResponse({'success': True})



def a_dashboard(request):
    return render(request,'ad.html')

def a_emp(request):
    return render(request,'admin-employees.html')

def a_playment(request):
    return render(request,'admin-payments.html')

def a_service(request):
    return render(request,'admin-services.html')
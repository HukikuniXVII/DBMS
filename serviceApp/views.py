from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect ,get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import datetime
from .forms import EditProfileForm,StaffForm,ReviewForm,BookingForm
from .models import Booking,Staff,Service,Payment,Review,TemporaryCustomer
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

            try:
                booking_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
            except KeyError:
                return JsonResponse({"status": "error", "message": "Date is missing."}, status=400)

            try:
                staff = Staff.objects.get(staff_id=data['staff'])
            except Staff.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Staff not found."}, status=400)

            try:
                service = Service.objects.get(service_id=data['service'])
            except Service.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Service not found."}, status=400)

            if request.user.is_authenticated:
                customer = request.user.id
            else:
                customer = None

            temp_customer = None
            if data.get('tempCustomer'):
                try:
                    temp_customer = TemporaryCustomer.objects.get(id=data['tempCustomer'])
                except TemporaryCustomer.DoesNotExist:
                    return JsonResponse({"status": "error", "message": "Temporary customer not found."}, status=400)

            if not customer and not temp_customer:
                return JsonResponse({"status": "error", "message": "No valid customer or temp_customer found."}, status=400)

            booking = Booking.objects.create(
                staff=staff,
                service=service,
                customer_id=customer,
                booking_date=booking_date,
                start_time=data['startTime'],  
                end_time=data['endTime'],  
                status='Pending',
                walk_in=data.get('walkIn', False),
                commission_amount=data.get('commissionAmount', 0.00),
                temp_customer=temp_customer,
            )

            if data.get('paymentMethod'):
                try:
                    amount = data.get('amount', 0.00)
                    payment = Payment.objects.create(
                        staff=staff,
                        payment_date=datetime.datetime.now(),
                        amount=amount,
                        payment_method=data['paymentMethod'],
                        status='Pending',
                        note=data.get('additionalNotes', ''),
                    )
                    booking.payment = payment
                    booking.save()
                except Exception as e:
                    return JsonResponse({"status": "error", "message": f"Error creating payment: {e}"}, status=400)

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
        return redirect('manage_staff')

    return render(request, 'edit_staff.html', {'staff': staff})

def delete_staff(request, staff_id):
    staff = get_object_or_404(Staff, pk=staff_id)
    staff.delete()
    return redirect('manage_staff')

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

def booking_list(request):
    # ดึงข้อมูลทั้งหมดของ booking
    bookings = Booking.objects.all().select_related('service', 'staff')
    
    # กรองข้อมูลว่าเป็น TemporaryCustomer หรือ Customer
    for booking in bookings:
        if booking.walk_in:  # ถ้า walk_in เป็น True
            # หากเป็น Walk-in จะใช้ TemporaryCustomer
            booking.customer_data = TemporaryCustomer.objects.filter(temp_customer_id=booking.temp_customer_id).first()
        else:
            # ถ้าไม่ใช่ Walk-in ใช้ Customer ปกติ
            booking.customer_data = booking.customer

    service_list = Service.objects.all()
    staff_list = Staff.objects.all()

    # สำหรับการ debug
    print("Bookings Data:")
    for booking in bookings:
        if booking.walk_in:
            # ตรวจสอบก่อนว่า customer_data เป็น None หรือไม่
            if booking.customer_data:
                customer_name = f"TempCustomer: {booking.customer_data.name}"
            else:
                customer_name = "TempCustomer: No data"
        else:
            # ถ้าเป็น Customer ปกติ
            if booking.customer_data:
                customer_name = f"Customer: {booking.customer_data.first_name} {booking.customer_data.last_name}"
            else:
                customer_name = "Customer: No data"

        print(f"Booking ID: {booking.booking_id}, Customer: {customer_name}")
        print(f"Service: {booking.service.name}, Staff: {booking.staff.name}")
        print(f"Booking Date: {booking.booking_date}, Status: {booking.status}")
        
    return render(request, 'admin-bookings.html', {
        'bookings': bookings, 
        'service_list': service_list, 
        'staff_list': staff_list
    })


def add_booking(request):
    if request.method == 'POST':
        try:
            print("Request method:", request.method)
            print("Form data:", request.POST)
            
            # Get data from the form
            phone = request.POST.get('phone')  # ใช้เบอร์โทร
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            booking_date = request.POST.get('booking_date')
            service_id = request.POST.get('service')
            staff_id = request.POST.get('staff')
            
            print("Phone:", phone)
            print("First Name:", first_name)
            print("Last Name:", last_name)
            print("Booking Date:", booking_date)
            print("Service ID:", service_id)
            print("Staff ID:", staff_id)

            # แปลงวันที่จาก input
            booking_date = datetime.datetime.strptime(booking_date, '%Y-%m-%dT%H:%M')

            # ดึงข้อมูลบริการและพนักงาน
            service = Service.objects.get(service_id=service_id)
            staff = Staff.objects.get(staff_id=staff_id)

            # สร้างลูกค้าชั่วคราวใน TemporaryCustomer
            temp_customer = TemporaryCustomer.objects.create(
                name=f"{first_name} {last_name}",
                phone=phone
            )

            print("Temporary Customer:", temp_customer)

            # สร้างการจอง
            booking = Booking(
                customer=None,  # กำหนดเป็น None หรือสามารถเชื่อมต่อกับลูกค้าปกติได้ถ้าจำเป็น
                temp_customer=temp_customer,  # เชื่อมโยงกับลูกค้าชั่วคราว
                service=service,
                staff=staff,
                booking_date=booking_date,
                status='Pending',
                walk_in=True,
            )
            booking.save()

            # Debug: print success message
            print("Booking created:", booking)

            messages.success(request, "Booking successfully created!")
            return redirect('admin-bookings')  # Adjust redirect URL as needed

        except Exception as e:
            # Catch any errors and print them
            print("Error during booking creation:", str(e))
            messages.error(request, "Error creating booking.")
            return render(request, 'admin-bookings.html', {'error': str(e)})

    else:
        # Handle GET request (if any)
        return render(request, 'admin-bookings.html')


def add_service(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        duration = request.POST.get('duration')
        price = request.POST.get('price')

        duration = int(duration)
        price = float(price) if price else 0.0  

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
        return redirect('manage_staff') 

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
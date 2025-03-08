from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect ,get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import datetime
from .forms import EditProfileForm,StaffForm,ReviewForm,BookingForm
from .models import Booking,Staff,Service,Payment,Review,TemporaryCustomer, TimeSlot
from loginApp.models import Customer
from django.contrib import messages
from django.db.models import Avg,Sum
import json
from django.db import transaction
from django.contrib.auth.decorators import login_required, user_passes_test

def superuser_required(user):
    return user.is_superuser

@user_passes_test(superuser_required)
def dashboard_stats(request):
    total_users = Customer.objects.count()
    total_bookings = Booking.objects.count()
    total_revenue = Booking.objects.aggregate(total=Sum('payment'))['total'] or 0

    return JsonResponse({
        "total_users": total_users,
        "total_bookings": total_bookings,
        "total_revenue": total_revenue
    })

@user_passes_test(superuser_required)
def dashboard_view(request):
    return render(request, 'ad.html')

@user_passes_test(superuser_required)
def admin_payments(request):
    payments = Payment.objects.all().prefetch_related(
        'payments_related_to_booking__service',  
        'payments_related_to_booking__staff'     
    )
    return render(request, 'admin-payments.html', {'payments': payments})


@user_passes_test(superuser_required)
def manage_reviews(request):
    reviews_list = Review.objects.all()
    return render(request, 'admin-reviews.html', {'reviews_list': reviews_list})

@user_passes_test(superuser_required)
def service_list(request):
    services = Service.objects.all()
    return render(request, 'service.html', {'services': services})

@user_passes_test(superuser_required)
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

@user_passes_test(superuser_required)
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

@user_passes_test(superuser_required)
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

@user_passes_test(superuser_required)
def delete_user(request, user_id):
    user = get_object_or_404(Customer, id=user_id)

    if request.method == 'POST':
        user.delete()
        return redirect('admin_users')

    return render(request, 'admin-users.html', {'user': user})

@user_passes_test(superuser_required)
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

@user_passes_test(superuser_required)
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

@user_passes_test(superuser_required)
def payment_methods(request):
    user = request.user
    customer = getattr(user, 'customer', None)

    if not customer:
        return JsonResponse({'error': 'Customer profile not found'}, status=404)

    payments = Payment.objects.filter(booking__customer_id=customer).values(
        'payment_id', 'amount', 'payment_date', 'payment_method', 'status'
    )

    return JsonResponse(list(payments), safe=False)

@user_passes_test(superuser_required)
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

@user_passes_test(superuser_required)
def booking_history(request):
    user = request.user
    customer = getattr(user, 'customer', None)

    if not customer:
        return JsonResponse({'error': 'Customer profile not found'}, status=404)

    bookings = Booking.objects.filter(customer_id=customer).values(
        'booking_id', 'booking_date', 'service__name', 'status'
    )

    return JsonResponse(list(bookings), safe=False)

@user_passes_test(superuser_required)
def booking_view(request):

    staff_list = Staff.objects.all()
    service_list = Service.objects.all()

    return render(request, 'booking1.html', {
        'staff_list': staff_list,
        'service_list': service_list,
    })

@user_passes_test(superuser_required)
def save_booking(request): #BOOKING HOME PAGE
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(f"Received data: {data}")

            booking_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
            start_time = datetime.datetime.strptime(data['startTime'], '%H:%M').time()
            end_time = datetime.datetime.strptime(data['endTime'], '%H:%M').time()

            # Fetch Staff
            try:
                staff = Staff.objects.get(staff_id=data['staff'])
            except Staff.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Staff not found."}, status=400)

            # Fetch Service
            try:
                service = Service.objects.get(service_id=data['service'])
            except Service.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Service not found."}, status=400)

            # ตรวจสอบว่า user login หรือไม่
            customer = request.user if request.user.is_authenticated else None

            temp_customer = None
            if data.get('tempCustomer'):
                try:
                    temp_customer = TemporaryCustomer.objects.get(id=data['tempCustomer'])
                    print(f"Temporary Customer: {temp_customer}")
                except TemporaryCustomer.DoesNotExist:
                    return JsonResponse({"status": "error", "message": "Temporary customer not found."}, status=400)

            if not customer and not temp_customer:
                return JsonResponse({"status": "error", "message": "No valid customer or temp_customer found."}, status=400)

            existing_slots = TimeSlot.objects.filter(
                staff=staff,
                slot_date=booking_date,
                status='booked'
            )
            print(f"Existing booked slots for {staff} on {booking_date}:")
            for slot in existing_slots:
                print(f"Start: {slot.start_time}, End: {slot.end_time}")

            time_slot_exists = existing_slots.filter(
                start_time__lt=end_time,  
                end_time__gt=start_time  
            ).exists()

            if time_slot_exists:
                return JsonResponse({"status": "error", "message": "TimeSlot already booked."}, status=400)

            with transaction.atomic():
                time_slot = TimeSlot.objects.create(
                    staff=staff,
                    slot_date=booking_date,
                    start_time=start_time,
                    end_time=end_time,
                    status='booked'
                )

                booking = Booking.objects.create(
                    staff=staff,
                    service=service,
                    customer=customer,
                    booking_date=booking_date,
                    start_time=start_time,
                    end_time=end_time,
                    status='Pending',
                    walk_in=data.get('walkIn', False),
                    commission_amount=(staff.commission_rate*service.price),
                    temp_customer=temp_customer,
                    slot=time_slot,
                )

                if data.get('paymentMethod'):
                    payment = Payment.objects.create(
                        staff=staff,
                        payment_date=datetime.datetime.now(),
                        amount=service.price,
                        payment_method=data['paymentMethod'],
                        status='Pending',
                        note=data.get('additionalNotes', '')
                    )
                    booking.payment = payment
                    booking.save()

            return JsonResponse({"status": "success", "message": "Booking saved!", "booking_id": booking.booking_id})

        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@user_passes_test(superuser_required)
def get_service_duration(request, service_id):
    try:
    
        service = Service.objects.get(service_id=service_id)

        return JsonResponse({'duration': service.duration})
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)

@user_passes_test(superuser_required)
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

@user_passes_test(superuser_required)
def booking1(request):
    return render(request,'booking1.html')

@user_passes_test(superuser_required)
def account(request):
    return render(request,'account.html')

@user_passes_test(superuser_required)
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

@user_passes_test(superuser_required)
def delete_staff(request, staff_id):
    staff = get_object_or_404(Staff, pk=staff_id)
    staff.delete()
    return redirect('manage_staff')

@user_passes_test(superuser_required)
def manage_services(request):
    service_list = Service.objects.all()
    return render(request, 'admin-services.html', {'service_list': service_list})

@user_passes_test(superuser_required)
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

@user_passes_test(superuser_required)
def delete_service(request, service_id):
    service = get_object_or_404(Service, service_id=service_id)
    service.delete()
    return redirect('admin-services')

@user_passes_test(superuser_required)
def booking_list(request):
    bookings = Booking.objects.all().select_related('service', 'staff')
    
    for booking in bookings:
        if booking.walk_in: 

            booking.customer_data = TemporaryCustomer.objects.filter(temp_customer_id=booking.temp_customer_id).first()
        else:

            booking.customer_data = booking.customer

    service_list = Service.objects.all()
    staff_list = Staff.objects.all()


    for booking in bookings:
        if booking.walk_in:

            if booking.customer_data:
                customer_name = f"TempCustomer: {booking.customer_data.name}"
            else:
                customer_name = "TempCustomer: No data"
        else:

            if booking.customer_data:
                customer_name = f"Customer: {booking.customer_data.first_name} {booking.customer_data.last_name}"
            else:
                customer_name = "Customer: No data"

    return render(request, 'admin-bookings.html', {
        'bookings': bookings, 
        'service_list': service_list, 
        'staff_list': staff_list
    })

#BOOKING ADMIN WALK_IN
@user_passes_test(superuser_required)
def add_booking(request): 
    if request.method == 'POST':
        try:
            phone = request.POST.get('phone')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            booking_date = datetime.datetime.strptime(request.POST.get('booking_date'), '%Y-%m-%dT%H:%M')
            service = Service.objects.get(service_id=request.POST.get('service'))
            staff = Staff.objects.get(staff_id=request.POST.get('staff'))

            booking_datetime = booking_date
            booking_date = booking_datetime.date()
            booking_time = booking_datetime.time()

            existing_time_slot = TimeSlot.objects.filter(
                staff=staff, 
                slot_date=booking_date, 
                status='booked',
                start_time__lt=booking_time, 
                end_time__gt=booking_time
            )

            if existing_time_slot.exists():
                messages.error(request, "TimeSlot already booked, please choose another time.")
                return render(request, 'admin-bookings.html')

            time_slot = TimeSlot.objects.create(
                staff=staff, 
                slot_date=booking_date, 
                start_time=booking_time,
                end_time=(datetime.datetime.combine(datetime.date.today(), booking_time) + datetime.timedelta(hours=1)).time(),
                status='booked'
            )

            temp_customer = TemporaryCustomer.objects.create(
                name=f"{first_name} {last_name}", 
                phone=phone
            )

            print(staff.commission_rate)
            print(service.price)

            booking = Booking.objects.create(
                temp_customer=temp_customer, 
                service=service, 
                staff=staff,
                slot=time_slot, 
                booking_date=booking_date, 
                status='Pending',
                walk_in=True, 
                commission_amount=(staff.commission_rate*service.price),
                start_time=booking_time, 
                end_time=time_slot.end_time
            )

            payment_method = 'cash'
            amount = service.price

            if payment_method and amount:
                print("Creating payment...")
                payment = Payment.objects.create(
                    staff=staff,
                    payment_date=datetime.datetime.now(),
                    amount=amount,
                    payment_method=payment_method,
                    payment_proof=None,
                    status='Pending',
                    note=request.POST.get('additionalNotes', '')
                )
                booking.payment = payment
                booking.save()
                print("Payment created successfully.")
            else:
                messages.error(request, "Missing payment data!")
            messages.success(request, "Booking successfully created!")
            return redirect('admin-bookings')

        except Exception as e:
            messages.error(request, f"Error creating booking: {str(e)}")
            return render(request, 'admin-bookings.html', {'error': str(e)})

    return render(request, 'admin-bookings.html')

@user_passes_test(superuser_required)
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

@user_passes_test(superuser_required)
def manage_staffs(request):
    staff_list = Staff.objects.all()
    return render(request, 'admin-employees.html', {'staff_list': staff_list})

@user_passes_test(superuser_required)
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

@user_passes_test(superuser_required)
def admin_users_view(request):
    customers = Customer.objects.all()
    return render(request, 'admin-users.html', {'customer': customers})

@user_passes_test(superuser_required)
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
    
    if status == 'Canceled':
        with transaction.atomic():
            payments = Payment.objects.filter(booking=booking)
            for payment in payments:
                payment.status = 'Canceled'
                payment.save()

        # ลบ TimeSlot ที่เกี่ยวข้องกับการจองนี้
        if booking.slot:
            booking.slot.delete()

    return JsonResponse({'success': True})

@user_passes_test(superuser_required)
def admin_timeslot(request):
    bookings = Booking.objects.select_related('service', 'staff', 'slot').all()
    
    events = []
    for booking in bookings:
        if booking.slot:  # ตรวจสอบว่ามี slot หรือไม่
            start_time = datetime.datetime.strptime(f"{booking.slot.slot_date} {booking.slot.start_time}", "%Y-%m-%d %H:%M:%S")
            end_time = datetime.datetime.strptime(f"{booking.slot.slot_date} {booking.slot.end_time}", "%Y-%m-%d %H:%M:%S")

            # กำหนดสีตามสถานะการจอง
            if booking.status == "Confirmed":
                color = "red"
            elif booking.status == "Pending":
                color = "#fceca9"
            else:
                color = "green"

            # ปรับ format วันที่เป็น วัน/เดือน (ภาษาไทย)
            formatted_date = start_time.strftime("%d/%b")  # เช่น 06/Mar

            events.append({
                "title": f"{booking.service.name} - {booking.staff.name}",
                "start": start_time.strftime("%Y-%m-%dT%H:%M:%S"),  # รูปแบบเวลาเป็น 24 ชั่วโมง
                "end": end_time.strftime("%Y-%m-%dT%H:%M:%S"),  # รูปแบบเวลาเป็น 24 ชั่วโมง
                "color": color,
                "formatted_date": formatted_date  # แสดงวันที่ในรูปแบบ วัน/เดือน
            })

    return render(request, 'admin-timeslot.html', {"events": events})

@user_passes_test(superuser_required)
def check_timeslot_availability(request):
    if request.method == "GET":
        # รับค่าจาก request
        date = request.GET.get('date')
        start_time = request.GET.get('start_time')
        staff_id = request.GET.get('staff_id')
        service_id = request.GET.get('service_id')  # รับ service_id เพื่อดึงระยะเวลาจากบริการ

        # เช็คว่าได้รับค่าทุกตัวหรือไม่
        if not date or not start_time or not staff_id or not service_id:
            return JsonResponse({"available": False, "message": "กรุณากรอกข้อมูลให้ครบถ้วน (date, start_time, staff_id, service_id)"})

        try:
            # ตรวจสอบรูปแบบของ start_time และแปลงให้เป็นรูปแบบที่ถูกต้อง
            try:
                booking_time = datetime.datetime.strptime(start_time, "%H:%M").time()
            except ValueError:
                # หากไม่ถูกต้องลองแปลงในรูปแบบ 12-hour และแปลงเป็น 24-hour
                try:
                    booking_time = datetime.datetime.strptime(start_time, "%I:%M %p").time()  # รูปแบบ 12-hour
                    start_time = datetime.datetime.strptime(str(booking_time), "%H:%M").strftime("%H:%M")  # แปลงเป็น 24-hour
                except ValueError:
                    return JsonResponse({"available": False, "message": "รูปแบบเวลาไม่ถูกต้อง กรุณาใช้รูปแบบ HH:MM หรือ HH:MM AM/PM"})

            # แปลงวันที่
            booking_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

            # Debug print ค่า date และ start_time
            print(f"Booking Date: {booking_date}, Booking Time: {booking_time}")

            # ดึงระยะเวลาบริการจาก service_id
            service = Service.objects.get(service_id=service_id)
            service_duration = service.duration  # รับระยะเวลาในรูปของ minutes หรือที่เหมาะสม

            # Debug print ค่า service_duration
            print(f"Service Duration: {service_duration} minutes")

            # คำนวณเวลา end_time
            start_datetime = datetime.datetime.combine(booking_date, booking_time)
            end_datetime = start_datetime + datetime.timedelta(minutes=service_duration)
            end_time = end_datetime.time()

            # Debug print ค่า end_time
            print(f"Calculated End Time: {end_time}")

            # ค้นหา TimeSlot ที่ตรงกับพนักงานและเวลา
            existing_time_slot = TimeSlot.objects.filter(
                staff_id=staff_id,
                slot_date=booking_date,
                start_time__lt=end_time,  # เช็คเวลาสิ้นสุด
                end_time__gt=booking_time,  # เช็คเวลาเริ่มต้น
                status='booked'
            ).exists()

            # Debug print ค่าผลลัพธ์จากการค้นหา TimeSlot
            print(f"Existing Time Slot Found: {existing_time_slot}")

            if existing_time_slot:
                return JsonResponse({"available": False, "message": "เวลานี้ถูกจองแล้ว โปรดเลือกเวลาอื่น"})
            return JsonResponse({"available": True})

        except Service.DoesNotExist:
            # Debug print เมื่อไม่พบบริการ
            print(f"Service with ID {service_id} not found.")
            return JsonResponse({"available": False, "message": "บริการนี้ไม่พบ"})
        except Exception as e:
            # Debug print เมื่อเกิดข้อผิดพลาด
            print(f"Error: {str(e)}")
            return JsonResponse({"available": False, "message": f"เกิดข้อผิดพลาด: {str(e)}"})

@user_passes_test(superuser_required)
def a_dashboard(request):
    return render(request,'ad.html')
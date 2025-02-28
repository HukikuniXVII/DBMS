from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages,auth
from django.contrib.auth import get_user_model
import traceback

def login_view(request):
    if request.method == "POST":
        loginEmail = request.POST["EMAIL"]
        loginPassword = request.POST["PWD"]
        try:
            user = auth.authenticate(request, username=loginEmail, password=loginPassword)

            if user is not None:
                login(request, user)
                return redirect('/booking1')
            else:
                messages.error(request, "ข้อมูลการเข้าสู่ระบบไม่ถูกต้อง")
                return redirect('/login')
                
        except Exception as e:
            messages.error(request, f"เกิดข้อผิดพลาดบางประการ: {str(e)}")
            return redirect('/login')
    else:
        return render(request, 'login.html')

User = get_user_model()

def register_view(request):
    if request.method == 'POST':
        register_email = request.POST['register_email']
        register_password = request.POST['register_password']
        register_firstName = request.POST['register_firstName']
        register_lastName = request.POST['register_lastName']
        register_phoneNumber = request.POST['register_phoneNumber']
        register_address = request.POST['register_address']
        register_birthDate = request.POST['register_birthDate']

        try:
            if User.objects.filter(email=register_email).exists():
                messages.error(request, "อีเมลนี้มีการใช้งานแล้ว")
                return redirect('/register')

            # Create a new user
            new_user = User.objects.create_user(
                username=register_email,  # You can use email as username or create another field for username
                email=register_email,
                password=register_password,  # The password will be hashed automatically
                first_name=register_firstName,
                last_name=register_lastName,
                phone=register_phoneNumber,
                address=register_address,
                birth_date=register_birthDate,
            )

            messages.success(request, "ลงทะเบียนสำเร็จ!")
            return redirect('/login')

        except Exception as e:
            messages.error(request, f"เกิดข้อผิดพลาดบางประการ: {traceback.format_exc()}")
            return redirect('/register')

    return render(request, 'register.html')

def logout(request):
    auth.logout(request)
    return redirect('/login')
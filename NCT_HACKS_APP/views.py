from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Preferences, UserModel
from django.core.files.storage import FileSystemStorage
def index(request):
    return render(request, 'index.html')

User = get_user_model()

def signup_view(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        username = request.POST['username']
        password = request.POST['password']
        date_of_birth = request.POST['date_of_birth']
        profile_photo = request.FILES.get('profile_photo', None)
        weight = request.POST['weight']
        height = request.POST['height']

        user = User.objects.create_user(username=username, password=password, first_name= first_name, last_name=last_name, email = email)

        custom_user = UserModel.objects.create(
            user=user,
            date_of_birth=date_of_birth,
            profile_photo=profile_photo,
            weight=weight,
            height=height
        )

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')  

    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid credentials')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')
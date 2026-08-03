from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect,HttpResponse, request
from django.urls import reverse
from .forms import CustomRegisterForm,CustomLoginForm
from django.contrib import messages
from django.contrib.auth import authenticate,login, logout
from django.contrib.auth.decorators import login_required


# Create your views here.
def register(request):
    if request.user.is_authenticated:
        return user_role(request)
    else:

        if request.method == "POST":
            form = CustomRegisterForm(request.POST)
            if form.is_valid():
                user=form.save()
                login(request, user) 
                messages.success(request, "Registration successful!")
                return user_role(request)
        else:
            form = CustomRegisterForm()
    return render(request,'register.html',{"form":form})

            
def auth_login(request):
    if request.user.is_authenticated:
        return user_role(request)
    else:
        if request.method == "POST":
            form = CustomLoginForm(request=request,data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                return user_role(request)
                
        else:
            form = CustomLoginForm()
    return render(request,'login.html',{'form':form})

def user_role(request):
    role_redirect = {
        "admin": "admin_dashboard",
        "teacher": "instructor_dashboard",
        "student": "student_dashboard",
    }

    return redirect(role_redirect.get(request.user.role, "login"))

def auth_logout(request):
    logout(request)
    return redirect('login')

@login_required
def admin_dashboard(request):
    return render(request,'dashboard/admin_dashboard.html')
@login_required
def student_dashboard(request):
    return render(request,'dashboard/student_dashboard.html')
@login_required
def instructor_dashboard(request):
    return render(request,'dashboard/instructor_dashboard.html')





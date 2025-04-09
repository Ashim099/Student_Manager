# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from rest_framework import viewsets
from .models import User, Program, Module, StudentProgram, Resource, Assignment, Submission, Result, Reminder, Announcement
from .serializers import (UserSerializer, ProgramSerializer, ModuleSerializer, StudentProgramSerializer,
                         ResourceSerializer, AssignmentSerializer, SubmissionSerializer,
                         ResultSerializer, ReminderSerializer, AnnouncementSerializer)

# API Viewsets
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

class ProgramViewSet(viewsets.ModelViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Program.objects.all()
        return Program.objects.filter(modules__teacher=self.request.user) | Program.objects.filter(studentprogram__student=self.request.user)

class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Module.objects.all()
        elif self.request.user.role == 'teacher':
            return Module.objects.filter(teacher=self.request.user)
        return Module.objects.filter(program__studentprogram__student=self.request.user)

class StudentProgramViewSet(viewsets.ModelViewSet):
    queryset = StudentProgram.objects.all()
    serializer_class = StudentProgramSerializer

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return StudentProgram.objects.all()
        return StudentProgram.objects.filter(student=self.request.user)

class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer

    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return Resource.objects.filter(uploaded_by=self.request.user)
        return Resource.objects.filter(module__program__studentprogram__student=self.request.user)

class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return Assignment.objects.filter(created_by=self.request.user)
        return Assignment.objects.filter(module__program__studentprogram__student=self.request.user)

class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer

    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return Submission.objects.filter(assignment__created_by=self.request.user)
        return Submission.objects.filter(student=self.request.user)

class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer

    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return Result.objects.filter(published_by=self.request.user)
        return Result.objects.filter(student=self.request.user)

class ReminderViewSet(viewsets.ModelViewSet):
    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer

    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user)

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer

    def get_queryset(self):
        if self.request.user.role == 'teacher':
            return Announcement.objects.filter(posted_by=self.request.user)
        return Announcement.objects.filter(module__program__studentprogram__student=self.request.user)

# Frontend Views
def homepage_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'student':
            return redirect('student_dashboard')
        elif request.user.role == 'teacher':
            return redirect('teacher_dashboard')
        elif request.user.role == 'admin':
            return redirect('admin_dashboard')
    return render(request, 'homepage.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'teacher':
                return redirect('teacher_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def student_dashboard_view(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('login')
    student_programs = StudentProgram.objects.filter(student=request.user)
    modules = Module.objects.filter(program__studentprogram__student=request.user)
    assignments = Assignment.objects.filter(module__program__studentprogram__student=request.user)
    context = {
        'student_programs': student_programs,
        'modules': modules,
        'assignments': assignments,
    }
    return render(request, 'student_dashboard.html', context)

def teacher_dashboard_view(request):
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('login')
    modules = Module.objects.filter(teacher=request.user)
    assignments = Assignment.objects.filter(created_by=request.user)
    context = {
        'modules': modules,
        'assignments': assignments,
    }
    return render(request, 'teacher_dashboard.html', context)

def admin_dashboard_view(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('login')
    users = User.objects.all()
    programs = Program.objects.all()
    context = {
        'users': users,
        'programs': programs,
    }
    return render(request, 'admin_dashboard.html', context)

def logout_view(request):
    logout(request)
    return redirect('homepage')
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils import timezone 
from datetime import timedelta, datetime
import datetime as dt
import random
import csv
import json
import pickle
from django_ratelimit.decorators import ratelimit
from .models import User, OTP, Program, Module, StudentProgram, Resource, Assignment, Submission, Result, Reminder, Announcement
from .forms import AdminAddUserForm
from django.http import HttpResponseForbidden, JsonResponse
from .forms import ResourceForm, AssignmentForm, AnnouncementForm, SubmissionForm, ReminderForm
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import joblib
import numpy as np
from .tasks import send_reminder_email
import logging

# Role-based access decorator
def role_required(role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect('login')
            if request.user.role != role and not request.user.is_superuser:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('homepage')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'teacher':
                return redirect('teacher_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

# Homepage View
def homepage_view(request):
    return render(request, 'homepage.html')

# Sign-Up View with Role Selection and OTP Verification
def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'signup.html')

        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            role=role,
            is_active=False
        )

        # Generate and send OTP
        otp = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=5)
        OTP.objects.create(user=user, otp=otp, expires_at=expires_at)
        send_mail(
            subject='Your OTP for Student Manager Sign-Up',
            message=f'Your OTP is {otp}. It is valid for 5 minutes.',
            from_email='yourgmail@gmail.com',
            recipient_list=[email],
            fail_silently=False,
        )
        request.session['signup_email'] = email
        return redirect('verify_otp_signup')

    return render(request, 'signup.html')

# Verify OTP for Sign-Up
def verify_otp_signup(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        email = request.session.get('signup_email')
        if not email:
            messages.error(request, 'Session expired. Please sign up again.')
            return redirect('signup')
        try:
            user = User.objects.get(email=email)
            otp_record = OTP.objects.filter(user=user, otp=otp).latest('created_at')
            if timezone.now() > otp_record.expires_at:
                messages.error(request, 'OTP has expired. Please sign up again.')
                user.delete()
                return redirect('signup')
            user.is_active = True
            user.save()
            otp_record.delete()
            user.backend = 'core.authentication.EmailBackend'
            login(request, user)
            # Safely delete session key
            if 'signup_email' in request.session:
                del request.session['signup_email']
            messages.success(request, 'Sign-up successful!')
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'teacher':
                return redirect('teacher_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
        except OTP.DoesNotExist:
            messages.error(request, 'Invalid OTP.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return render(request, 'verify_otp_signup.html')

# Generic Login View with Role-Based OTP Verification
def login_with_email(request, role):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, role=role)
            otp = str(random.randint(100000, 999999))
            expires_at = timezone.now() + timedelta(minutes=5)
            OTP.objects.create(user=user, otp=otp, expires_at=expires_at)
            send_mail(
                subject=f'Your OTP for Student Manager {role.capitalize()} Login',
                message=f'Your OTP is {otp}. It is valid for 5 minutes.',
                from_email='yourgmail@gmail.com',
                recipient_list=[email],
                fail_silently=False,
            )
            request.session['login_email'] = email
            request.session['login_role'] = role
            return redirect('verify_otp')
        except User.DoesNotExist:
            messages.error(request, f'No {role} found with this email.')
        except Exception as e:
            messages.error(request, f'Error sending OTP: {str(e)}')
    return render(request, f'login_{role}.html')

# Role-Specific Login Views
def student_login(request):
    return login_with_email(request, 'student')

def teacher_login(request):
    return login_with_email(request, 'teacher')

def admin_login(request):
    return login_with_email(request, 'admin')

# Verify OTP for Login
def verify_otp(request):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        email = request.session.get('login_email')
        role = request.session.get('login_role')
        if not email or not role:
            messages.error(request, 'Session expired. Please try logging in again.')
            return redirect('homepage')
        try:
            user = User.objects.get(email=email, role=role)
            otp_record = OTP.objects.filter(user=user, otp=otp).latest('created_at')
            if timezone.now() > otp_record.expires_at:
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect(f'{role}_login')
            user.backend = 'core.authentication.EmailBackend'
            login(request, user)
            otp_record.delete()
            # Safely delete session keys
            if 'login_email' in request.session:
                del request.session['login_email']
            if 'login_role' in request.session:
                del request.session['login_role']
            messages.success(request, 'Login successful!')
            if user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'teacher':
                return redirect('teacher_dashboard')
            elif user.role == 'admin':
                return redirect('admin_dashboard')
        except OTP.DoesNotExist:
            messages.error(request, 'Invalid OTP.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return render(request, 'verify_otp.html')

# Logout View
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('homepage')

# Admin Dashboard View
@login_required
@role_required('admin')
def admin_dashboard_view(request):
    users = User.objects.all()
    programs = Program.objects.all()
    modules = Module.objects.all()
    context = {
        'users': users,
        'programs': programs,
        'modules': modules,
    }
    return render(request, 'admin_dashboard.html', context)

# Admin: Add User
@login_required
@role_required('admin')
def admin_add_user(request):
    if request.method == 'POST':
        form = AdminAddUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} added successfully.')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminAddUserForm()
    return render(request, 'admin_add_user.html', {'form': form})

# Admin: Edit User
@login_required
@role_required('admin')
def admin_edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = AdminAddUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully.')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminAddUserForm(instance=user)
    return render(request, 'admin_edit_user.html', {'form': form, 'user': user})

# Admin: Delete User
@login_required
@role_required('admin')
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('admin_dashboard')
    user.delete()
    messages.success(request, f'User {user.username} deleted successfully.')
    return redirect('admin_dashboard')

# Admin: Create Program
@login_required
@role_required('admin')
def admin_create_program(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        Program.objects.create(name=name, description=description, created_by=request.user)
        messages.success(request, 'Program created successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin_create_program.html')

# Admin: Edit Program
@login_required
@role_required('admin')
def admin_edit_program(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    if request.method == 'POST':
        program.name = request.POST.get('name')
        program.description = request.POST.get('description')
        program.save()
        messages.success(request, 'Program updated successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin_edit_program.html', {'program': program})

# Admin: Delete Program
@login_required
@role_required('admin')
def admin_delete_program(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    program.delete()
    messages.success(request, 'Program deleted successfully.')
    return redirect('admin_dashboard')

# Admin: Create Module
@login_required
@role_required('admin')
def admin_create_module(request):
    programs = Program.objects.all()
    teachers = User.objects.filter(role='teacher')
    if not teachers.exists():
        messages.warning(request, 'No teachers available. Please add a teacher first.')
        return redirect('admin_add_user')
    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        program_id = request.POST.get('program')
        teacher_id = request.POST.get('teacher')
        program = get_object_or_404(Program, id=program_id)
        teacher = get_object_or_404(User, id=teacher_id, role='teacher') if teacher_id else None
        Module.objects.create(code=code, name=name, program=program, teacher=teacher)
        messages.success(request, 'Module created successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin_create_module.html', {'programs': programs, 'teachers': teachers})

# Admin: Edit Module
@login_required
@role_required('admin')
def admin_edit_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    programs = Program.objects.all()
    teachers = User.objects.filter(role='teacher')
    if not teachers.exists():
        messages.warning(request, 'No teachers available. Please add a teacher first.')
        return redirect('admin_add_user')
    if request.method == 'POST':
        module.code = request.POST.get('code')
        module.name = request.POST.get('name')
        program_id = request.POST.get('program')
        teacher_id = request.POST.get('teacher')
        module.program = get_object_or_404(Program, id=program_id)
        module.teacher = get_object_or_404(User, id=teacher_id, role='teacher') if teacher_id else None
        module.save()
        messages.success(request, 'Module updated successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin_edit_module.html', {'module': module, 'programs': programs, 'teachers': teachers})

# Admin: Delete Module
@login_required
@role_required('admin')
def admin_delete_module(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    module.delete()
    messages.success(request, 'Module deleted successfully.')
    return redirect('admin_dashboard')

# Admin: Assign Teacher to Module
@login_required
@role_required('admin')
def admin_assign_teacher(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    teachers = User.objects.filter(role='teacher')
    if not teachers.exists():
        messages.warning(request, 'No teachers available. Please add a teacher first.')
        return redirect('admin_add_user')
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher')
        teacher = get_object_or_404(User, id=teacher_id, role='teacher')
        module.teacher = teacher
        module.save()
        messages.success(request, 'Teacher assigned successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin_assign_teacher.html', {'module': module, 'teachers': teachers})

# Admin: Enroll Student in Program
@login_required
@role_required('admin')
def admin_enroll_student(request, program_id):
    program = get_object_or_404(Program, id=program_id)
    if request.method == 'POST':
        student_id = request.POST.get('student')
        student = get_object_or_404(User, id=student_id, role='student')
        if StudentProgram.objects.filter(student=student, program=program).exists():
            messages.error(request, 'Student is already enrolled in this program.')
        else:
            StudentProgram.objects.create(student=student, program=program)
            messages.success(request, 'Student enrolled successfully.')
        return redirect('admin_dashboard')
    students = User.objects.filter(role='student')
    if not students.exists():
        messages.warning(request, 'No students available. Please add a student first.')
        return redirect('admin_add_user')
    return render(request, 'admin_enroll_student.html', {'program': program, 'students': students})

# Student Dashboard View
@login_required
@role_required('student')
def student_dashboard_view(request):
    if request.user.role != 'student':
        messages.error(request, "Access denied: You are not a student.")
        return redirect('login')

    student = request.user
    programs = student.enrolled_programs.all()
    modules = Module.objects.filter(program__in=programs.values('program'))
    
    announcements = Announcement.objects.filter(module__in=modules)
    assignments = Assignment.objects.filter(module__in=modules)
    resources = Resource.objects.filter(module__in=modules)
    results = Result.objects.filter(student=student)
    reminders = Reminder.objects.filter(student=student)
    submissions = Submission.objects.filter(student=student)
    
    program_name = programs.first().program.name if programs.exists() else "No Program"

    context = {
        'announcements': announcements,
        'assignments': assignments,
        'resources': resources,
        'results': results,
        'reminders': reminders,
        'programs': programs,
        'submissions': submissions,
        'program_name': program_name,
    }
    return render(request, 'student_dashboard.html', context)

# Student: Choose Program
@login_required
@role_required('student')
def student_choose_program(request):
    programs = Program.objects.all()
    if request.method == 'POST':
        program_id = request.POST.get('program')
        program = get_object_or_404(Program, id=program_id)
        StudentProgram.objects.create(student=request.user, program=program)
        messages.success(request, 'Program enrolled successfully.')
        return redirect('student_dashboard')
    return render(request, 'student_choose_program.html', {'programs': programs})

# Student: Pomodoro Timer
@login_required
@role_required('student')
def student_pomodoro_timer(request):
    return render(request, 'student_pomodoro_timer.html')

# Student: Set Reminder
@login_required
@role_required('student')
def student_set_reminder(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        reminder_date = request.POST.get('due_date')
        Reminder.objects.create(student=request.user, title=title, reminder_date=reminder_date)
        messages.success(request, 'Reminder set successfully.')
        return redirect('student_dashboard')
    return render(request, 'student_set_reminder.html')

# Student: Submit Assignment
@login_required
@role_required('student')
def student_submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    student = request.user
    
    # Check if student is enrolled in the assignment's module
    if not assignment.module.program.studentprogram_set.filter(student=student).exists():
        return HttpResponseForbidden("You are not enrolled in this module.")
    
    submission, created = Submission.objects.get_or_create(
        student=student,
        assignment=assignment,
        defaults={'submitted_at': timezone.now()}
    )
    
    if request.method == "POST":
        form = SubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment submitted successfully!")
            return redirect('student_dashboard')
    else:
        form = SubmissionForm(instance=submission)
    
    context = {
        'form': form,
        'assignment': assignment,
    }
    return render(request, 'student_submit_assignment.html', context)

# Student create reminders
logger = logging.getLogger(__name__)
@login_required
@role_required('student')
def create_reminder(request):
    logger.info("Entering create_reminder view")
    if request.method == 'POST':
        logger.info("Received POST request")
        form = ReminderForm(request.POST)
        if form.is_valid():
            logger.info("Form is valid")
            # Check if the user is a student
            if request.user.role != 'student':
                logger.error(f"User {request.user.email} is not a student (role: {request.user.role})")
                messages.error(request, "Only students can create reminders.")
                return redirect('student_dashboard')
            
            reminder = form.save(commit=False)
            reminder.student = request.user  # Set directly to the user
            reminder.save()
            reminder_date = form.cleaned_data['reminder_date']
            delay = (reminder_date - timezone.now()).total_seconds()
            logger.info(f"Scheduling reminder email for reminder {reminder.id} at {reminder_date}, delay: {delay} seconds")
            send_reminder_email(reminder.id, schedule=int(delay))
            messages.success(request, 'Reminder created successfully!')
            return redirect('student_dashboard')
        else:
            logger.error(f"Form is invalid: {form.errors}")
    else:
        logger.info("Received GET request")
        form = ReminderForm()
    return render(request, 'student_create_reminder.html', {'form': form})



def student_edit_reminder(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id, student=request.user)
    if request.method == "POST":
        form = ReminderForm(request.POST, instance=reminder)
        if form.is_valid():
            form.save()
            messages.success(request, "Reminder updated successfully!")
            return redirect('student_dashboard')
    else:
        form = ReminderForm(instance=reminder)
    return render(request, 'student_edit_reminder.html', {'form': form, 'reminder': reminder})

@login_required
def student_delete_reminder(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id, student__id=request.user.id)
    if request.method == "POST":
        reminder.delete()
        messages.success(request, "Reminder deleted successfully!")
        return redirect('student_dashboard')
    return render(request, 'student_confirm_delete.html', {'object': reminder})

# Teacher Dashboard View
@login_required
@role_required('teacher')
def teacher_dashboard_view(request):
    teacher = request.user
    modules = Module.objects.filter(teacher=teacher)

    for module in modules:
        results = Result.objects.filter(module=module)
        total_students = StudentProgram.objects.filter(program=module.program).count()
        module.passing_percentage = (
            (results.filter(grade__gte=50).count() / total_students) * 100
            if total_students > 0 else 0
        )

    context = {
        'modules': modules,
        'resources': Resource.objects.filter(uploaded_by=teacher),
        'assignments': Assignment.objects.filter(created_by=teacher),
        'announcements': Announcement.objects.filter(created_by=teacher),
        'submissions': Submission.objects.filter(assignment__created_by=teacher),
        
    }
    return render(request, 'teacher_dashboard.html', context)


# Teacher: Manage Resources (CRUD - Create)
@login_required
@role_required('teacher')
def teacher_manage_resources(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if module.teacher != request.user:
        messages.error(request, 'You do not have permission to manage resources for this module.')
        return redirect('teacher_dashboard')
    if request.method == 'POST':
        title = request.POST.get('title')
        file = request.FILES.get('file')
        Resource.objects.create(title=title, module=module, file=file, uploaded_by=request.user)
        messages.success(request, 'Resource uploaded successfully.')
        return redirect('teacher_dashboard')
    return render(request, 'teacher_manage_resources.html', {'module': module})

def teacher_edit_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id, uploaded_by=request.user)
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Resource updated successfully!")
            return redirect('teacher_manage_resources', module_id=resource.module.id)
    else:
        form = ResourceForm(instance=resource)
    return render(request, 'teacher_edit_resource.html', {'form': form, 'resource': resource})

# Teacher: Delete Resource (CRUD - Delete)
@login_required
@role_required('teacher')
def teacher_delete_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id, uploaded_by=request.user)
    if request.method == "POST":
        resource.delete()
        messages.success(request, "Resource deleted successfully!")
        return redirect('teacher_manage_resources', module_id=resource.module.id)
    return render(request, 'teacher_confirm_delete.html', {'object': resource})

# Teacher: Share Assignment
@login_required
@role_required('teacher')
def teacher_share_assignment(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if module.teacher != request.user:
        messages.error(request, 'You do not have permission to share assignments for this module.')
        return redirect('teacher_dashboard')
    if request.method == 'POST':
        title = request.POST.get('title')
        due_date = request.POST.get('due_date')
        description = request.POST.get('description', '')
        Assignment.objects.create(title=title, description=description, module=module, due_date=due_date, created_by=request.user)
        messages.success(request, 'Assignment shared successfully.')
        return redirect('teacher_dashboard')
    return render(request, 'teacher_share_assignment.html', {'module': module})

def teacher_edit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, created_by=request.user)
    if request.method == "POST":
        form = AssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment updated successfully!")
            return redirect('teacher_dashboard')
    else:
        form = AssignmentForm(instance=assignment)
    return render(request, 'teacher_edit_assignment.html', {'form': form, 'assignment': assignment})

def teacher_delete_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, created_by=request.user)
    if request.method == "POST":
        assignment.delete()
        messages.success(request, "Assignment deleted successfully!")
        return redirect('teacher_dashboard')
    return render(request, 'teacher_confirm_delete.html', {'object': assignment})

# Teacher: Post Announcement
@login_required
@role_required('teacher')
def teacher_post_announcement(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if module.teacher != request.user:
        messages.error(request, 'You do not have permission to post announcements for this module.')
        return redirect('teacher_dashboard')
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        file = request.FILES.get('file') if 'file' in request.FILES else None
        Announcement.objects.create(title=title, content=content, module=module, file=file, created_by=request.user)
        messages.success(request, 'Announcement posted successfully.')
        return redirect('teacher_dashboard')
    return render(request, 'teacher_post_announcement.html', {'module': module})

def teacher_edit_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id, created_by=request.user)
    if request.method == "POST":
        form = AnnouncementForm(request.POST, request.FILES, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Announcement updated successfully!")
            return redirect('teacher_dashboard')
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'teacher_edit_announcement.html', {'form': form, 'announcement': announcement})

# Teacher: Delete announcements
def teacher_delete_announcement(request, announcement_id):
    announcement = get_object_or_404(Announcement, id=announcement_id, created_by=request.user)
    if request.method == "POST":
        announcement.delete()
        messages.success(request, "Announcement deleted successfully!")
        return redirect('teacher_dashboard')
    return render(request, 'teacher_confirm_delete.html', {'object': announcement})

# Teacher: Publish Result
@login_required
@role_required('teacher')
def teacher_publish_result(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    teacher = request.user

    # Verify the teacher is assigned to the module
    if module.teacher != teacher:
        return HttpResponseForbidden("You are not authorized to publish results for this module.")

    # Get students in the module's program
    students = User.objects.filter(enrolled_programs__program=module.program, role='student')

    if request.method == "POST":
        # Handle form submission to publish results
        for student in students:
            grade = request.POST.get(f'grade_{student.id}')
            if grade:
                Result.objects.update_or_create(
                    student=student,
                    module=module,
                    defaults={'grade': grade}
                )
        messages.success(request, "Results published successfully!")
        return redirect('teacher_dashboard')

    # GET request: Display form to input grades
    context = {
        'module': module,
        'students': students,
    }
    return render(request, 'teacher_publish_result.html', context)

@login_required
def student_course_recommendation(request):
    if request.user.role != 'student':
        messages.error(request, "Access denied: You are not a student.")
        return redirect('login')

    return render(request, 'student_course_recommendation.html', {})

@login_required
def search_course_recommendation(request):
    if request.user.role != 'student':
        return JsonResponse({'error': 'Access denied: You are not a student.'}, status=403)

    search_term = request.GET.get('term', '').strip().lower()
    csv_path = r"D:\StudentManager\core\UdemyCleanedTitle.csv"
    courses = []

    if not search_term:  # Return empty list for empty search term
        return JsonResponse({'courses': []})

    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                title = row['course_title'].lower()  # Use course_title for searching
                if search_term in title:
                    courses.append({
                        'title': row['Clean_title'],  # Use Clean_title for display
                        'url': row['url']
                    })
                if len(courses) >= 10:  # Limit to 10 suggestions
                    break
    except FileNotFoundError:
        return JsonResponse({'courses': [], 'error': 'Course data not found.'})
    except KeyError as e:
        return JsonResponse({'courses': [], 'error': f'Missing column: {e}'})

    return JsonResponse({'courses': courses})

@login_required
def student_gpa_prediction(request):
    if request.user.role != 'student':
        messages.error(request, "Access denied: You are not a student.")
        return redirect('login')

    predicted_gpa = None
    predicted_grade = None

    if request.method == 'POST':
        try:
            # Extract form data
            attendance_rate = float(request.POST.get('attendance_rate', 0))
            study_hours = float(request.POST.get('study_hours', 0))
            previous_grade = float(request.POST.get('previous_grade', 0))
            extracurricular_hours = float(request.POST.get('extracurricular_hours', 0))
            parental_support = float(request.POST.get('parental_support', 0))

            # Validate inputs
            if not (0 <= attendance_rate <= 100):
                messages.error(request, "Attendance Rate must be between 0 and 100.")
                return render(request, 'student_gpa_prediction.html', {})
            if not (0 <= study_hours <= 168):
                messages.error(request, "Study Hours per Week must be between 0 and 168.")
                return render(request, 'student_gpa_prediction.html', {})
            if not (0 <= previous_grade <= 100):
                messages.error(request, "Previous Grade must be between 0 and 100.")
                return render(request, 'student_gpa_prediction.html', {})
            if not (0 <= extracurricular_hours <= 10):
                messages.error(request, "Extracurricular Hours must be between 0 and 10.")
                return render(request, 'student_gpa_prediction.html', {})
            if not (0 <= parental_support <= 2):  # Adjusted based on LabelEncoder: High=0, Low=1, Medium=2
                messages.error(request, "Parental Support must be between 0 and 2 (0=High, 1=Low, 2=Medium).")
                return render(request, 'student_gpa_prediction.html', {})

            # Load the ML model
            model_path = r"D:\StudentManager\core\ml_models\gpa_prediction_model.pkl"
            try:
                model = joblib.load(model_path)
            except Exception as e:
                messages.error(request, f"Error loading the GPA prediction model: {str(e)}")
                return render(request, 'student_gpa_prediction.html', {})

            # Prepare input for the model
            input_data = np.array([[attendance_rate, study_hours, previous_grade, extracurricular_hours, parental_support]])

            # Make prediction
            predicted_grade = model.predict(input_data)[0]
            predicted_grade = max(0, min(100, predicted_grade))  # Clamp between 0 and 100

            # Convert to GPA (4.0 scale)
            if predicted_grade >= 90:
                predicted_gpa = 4.0
            elif predicted_grade >= 80:
                predicted_gpa = 3.0
            elif predicted_grade >= 70:
                predicted_gpa = 2.0
            elif predicted_grade >= 60:
                predicted_gpa = 1.0
            else:
                predicted_gpa = 0.0

        except ValueError:
            messages.error(request, "Please enter valid numbers for all fields.")
            return render(request, 'student_gpa_prediction.html', {})

    context = {
        'predicted_gpa': predicted_gpa,
        'predicted_grade': predicted_grade,
    }
    return render(request, 'student_gpa_prediction.html', context)
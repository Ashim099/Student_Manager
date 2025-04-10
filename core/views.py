from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
from ratelimit.decorators import ratelimit
from .models import User, OTP, Program, Module, StudentProgram, Resource, Assignment, Submission, Result, Reminder, Announcement
from ml_models.gpa_predictor import predict_gpa
from ml_models.course_recommender import recommend_courses

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
            is_active=False  # User will be activated after OTP verification
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
            del request.session['signup_email']
            login(request, user)
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
            login(request, user)
            otp_record.delete()
            del request.session['login_email']
            del request.session['login_role']
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
def admin_dashboard_view(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('homepage')
    users = User.objects.all()
    programs = Program.objects.all()
    modules = Module.objects.all()
    context = {
        'users': users,
        'programs': programs,
        'modules': modules,
    }
    return render(request, 'admin_dashboard.html', context)

# Admin: Create Program
def admin_create_program(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('homepage')
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        Program.objects.create(name=name, description=description, created_by=request.user)
        messages.success(request, 'Program created successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin_create_program.html')

# Admin: Create Module
def admin_create_module(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('homepage')
    programs = Program.objects.all()
    teachers = User.objects.filter(role='teacher')
    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        program_id = request.POST.get('program')
        teacher_id = request.POST.get('teacher')
        program = Program.objects.get(id=program_id)
        teacher = User.objects.get(id=teacher_id) if teacher_id else None
        Module.objects.create(code=code, name=name, program=program, teacher=teacher)
        messages.success(request, 'Module created successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin_create_module.html', {'programs': programs, 'teachers': teachers})

# Admin: Assign Teacher to Module
def admin_assign_teacher(request, module_id):
    if not request.user.is_authenticated or request.user.role != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('homepage')
    module = Module.objects.get(id=module_id)
    teachers = User.objects.filter(role='teacher')
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher')
        teacher = User.objects.get(id=teacher_id)
        module.teacher = teacher
        module.save()
        messages.success(request, 'Teacher assigned successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin_assign_teacher.html', {'module': module, 'teachers': teachers})

# Student Dashboard View
def student_dashboard_view(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('homepage')
    student_programs = StudentProgram.objects.filter(student=request.user)
    modules = Module.objects.filter(program__studentprogram__student=request.user)
    resources = Resource.objects.filter(module__program__studentprogram__student=request.user)
    assignments = Assignment.objects.filter(module__program__studentprogram__student=request.user)
    results = Result.objects.filter(student=request.user)
    reminders = Reminder.objects.filter(user=request.user)
    context = {
        'student_programs': student_programs,
        'modules': modules,
        'resources': resources,
        'assignments': assignments,
        'results': results,
        'reminders': reminders,
    }
    return render(request, 'student_dashboard.html', context)

# Student: Choose Program
def student_choose_program(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('homepage')
    programs = Program.objects.all()
    if request.method == 'POST':
        program_id = request.POST.get('program')
        program = Program.objects.get(id=program_id)
        StudentProgram.objects.create(student=request.user, program=program)
        messages.success(request, 'Program enrolled successfully.')
        return redirect('student_dashboard')
    return render(request, 'student_choose_program.html', {'programs': programs})

# Student: GPA Prediction
def student_gpa_prediction(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('homepage')
    if request.method == 'POST':
        grades = Ang = [float(request.POST.get(f'grade_{i}', 0)) for i in range(1, 4) if request.POST.get(f'grade_{i}')]
        attendance = float(request.POST.get('attendance', 0))
        student_data = {'grades': grades, 'attendance': attendance}
        predicted_gpa = predict_gpa(student_data)
        return render(request, 'student_gpa_prediction.html', {'predicted_gpa': predicted_gpa})
    return render(request, 'student_gpa_prediction.html')

# Student: Course Recommendation
def student_course_recommendation(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('homepage')
    if request.method == 'POST':
        interests = request.POST.get('interests', '').split(',')
        student_data = {'interests': [interest.strip() for interest in interests]}
        recommended_courses = recommend_courses(student_data)
        return render(request, 'student_course_recommendation.html', {'recommended_courses': recommended_courses})
    return render(request, 'student_course_recommendation.html')

# Student: Pomodoro Timer
def student_pomodoro_timer(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('homepage')
    return render(request, 'student_pomodoro_timer.html')

# Student: Set Reminder
def student_set_reminder(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('homepage')
    if request.method == 'POST':
        title = request.POST.get('title')
        due_date = request.POST.get('due_date')
        Reminder.objects.create(user=request.user, title=title, due_date=due_date)
        messages.success(request, 'Reminder set successfully.')
        return redirect('student_dashboard')
    return render(request, 'student_set_reminder.html')

# Student: Submit Assignment
def student_submit_assignment(request, assignment_id):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('homepage')
    assignment = Assignment.objects.get(id=assignment_id)
    if request.method == 'POST':
        file = request.FILES.get('file')
        Submission.objects.create(student=request.user, assignment=assignment, file=file)
        messages.success(request, 'Assignment submitted successfully.')
        return redirect('student_dashboard')
    return render(request, 'student_submit_assignment.html', {'assignment': assignment})

# Teacher Dashboard View
def teacher_dashboard_view(request):
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('homepage')
    modules = Module.objects.filter(teacher=request.user)
    resources = Resource.objects.filter(uploaded_by=request.user)
    assignments = Assignment.objects.filter(created_by=request.user)
    announcements = Announcement.objects.filter(posted_by=request.user)
    context = {
        'modules': modules,
        'resources': resources,
        'assignments': assignments,
        'announcements': announcements,
    }
    return render(request, 'teacher_dashboard.html', context)

# Teacher: Manage Resources (CRUD - Create)
def teacher_manage_resources(request, module_id):
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('homepage')
    module = Module.objects.get(id=module_id)
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

# Teacher: Delete Resource (CRUD - Delete)
def teacher_delete_resource(request, resource_id):
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('homepage')
    resource = Resource.objects.get(id=resource_id)
    if resource.uploaded_by != request.user:
        messages.error(request, 'You do not have permission to delete this resource.')
        return redirect('teacher_dashboard')
    resource.delete()
    messages.success(request, 'Resource deleted successfully.')
    return redirect('teacher_dashboard')

# Teacher: Share Assignment
def teacher_share_assignment(request, module_id):
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('homepage')
    module = Module.objects.get(id=module_id)
    if module.teacher != request.user:
        messages.error(request, 'You do not have permission to share assignments for this module.')
        return redirect('teacher_dashboard')
    if request.method == 'POST':
        title = request.POST.get('title')
        due_date = request.POST.get('due_date')
        Assignment.objects.create(title=title, module=module, due_date=due_date, created_by=request.user)
        messages.success(request, 'Assignment shared successfully.')
        return redirect('teacher_dashboard')
    return render(request, 'teacher_share_assignment.html', {'module': module})

# Teacher: Post Announcement
def teacher_post_announcement(request, module_id):
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('homepage')
    module = Module.objects.get(id=module_id)
    if module.teacher != request.user:
        messages.error(request, 'You do not have permission to post announcements for this module.')
        return redirect('teacher_dashboard')
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        Announcement.objects.create(title=title, content=content, module=module, posted_by=request.user)
        messages.success(request, 'Announcement posted successfully.')
        return redirect('teacher_dashboard')
    return render(request, 'teacher_post_announcement.html', {'module': module})

# Teacher: Publish Result
def teacher_publish_result(request, module_id):
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('homepage')
    module = Module.objects.get(id=module_id)
    if module.teacher != request.user:
        messages.error(request, 'You do not have permission to publish results for this module.')
        return redirect('teacher_dashboard')
    students = User.objects.filter(studentprogram_set__program=module.program, role='student')
    if request.method == 'POST':
        for student in students:
            grade = request.POST.get(f'grade_{student.id}')
            if grade:
                Result.objects.create(student=student, module=module, grade=float(grade), published_by=request.user)
        messages.success(request, 'Results published successfully.')
        return redirect('teacher_dashboard')
    return render(request, 'teacher_publish_result.html', {'module': module, 'students': students})
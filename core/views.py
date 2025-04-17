from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
from django_ratelimit.decorators import ratelimit
from .models import User, OTP, Program, Module, StudentProgram, Resource, Assignment, Submission, Result, Reminder, Announcement
from .forms import AdminAddUserForm

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
            del request.session['signup_email']
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
    student_programs = StudentProgram.objects.filter(student=request.user)
    if not student_programs.exists():
        messages.info(request, 'Please choose a program to continue.')
        return redirect('student_choose_program')
    
    modules = Module.objects.filter(program__studentprogram__student=request.user)
    resources = Resource.objects.filter(module__program__studentprogram__student=request.user)
    assignments = Assignment.objects.filter(module__program__studentprogram__student=request.user)
    results = Result.objects.filter(student=request.user)
    reminders = Reminder.objects.filter(student=request.user)
    enrolled_modules = Module.objects.filter(program__in=[sp.program for sp in student_programs])
    student_announcements = Announcement.objects.filter(module__in=enrolled_modules)
    
    context = {
        'student_programs': student_programs,
        'modules': modules,
        'resources': resources,
        'assignments': assignments,
        'results': results,
        'reminders': reminders,
        'student_announcements': student_announcements,
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
    if request.method == 'POST':
        file = request.FILES.get('file')
        Submission.objects.create(student=request.user, assignment=assignment, file=file)
        messages.success(request, 'Assignment submitted successfully.')
        return redirect('student_dashboard')
    return render(request, 'student_submit_assignment.html', {'assignment': assignment})

# Teacher Dashboard View
@login_required
@role_required('teacher')
def teacher_dashboard_view(request):
    teacher_modules = Module.objects.filter(teacher=request.user)
    for module in teacher_modules:
        results = Result.objects.filter(module=module)
        total_students = StudentProgram.objects.filter(program=module.program).count()
        if total_students > 0:
            passing_students = results.filter(grade__gte=50).count()
            module.passing_percentage = (passing_students / total_students) * 100
        else:
            module.passing_percentage = 0
    resources = Resource.objects.filter(uploaded_by=request.user)
    assignments = Assignment.objects.filter(created_by=request.user)
    announcements = Announcement.objects.filter(created_by=request.user)
    context = {
        'teacher_modules': teacher_modules,
        'resources': resources,
        'assignments': assignments,
        'announcements': announcements,
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

# Teacher: Delete Resource (CRUD - Delete)
@login_required
@role_required('teacher')
def teacher_delete_resource(request, resource_id):
    resource = get_object_or_404(Resource, id=resource_id)
    if resource.uploaded_by != request.user:
        messages.error(request, 'You do not have permission to delete this resource.')
        return redirect('teacher_dashboard')
    resource.delete()
    messages.success(request, 'Resource deleted successfully.')
    return redirect('teacher_dashboard')

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

# Teacher: Publish Result
@login_required
@role_required('teacher')
def teacher_publish_result(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    if module.teacher != request.user:
        messages.error(request, 'You do not have permission to publish results for this module.')
        return redirect('teacher_dashboard')
    students = User.objects.filter(studentprogram_set__program=module.program, role='student')
    if request.method == 'POST':
        for student in students:
            grade = request.POST.get(f'grade_{student.id}')
            if grade:
                Result.objects.create(student=student, module=module, grade=float(grade))
        messages.success(request, 'Results published successfully.')
        return redirect('teacher_dashboard')
    return render(request, 'teacher_publish_result.html', {'module': module, 'students': students})

# Commented ML Model Views (to be implemented later)
'''
# Student: GPA Prediction
def student_gpa_prediction(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('homepage')
    if request.method == 'POST':
        grades = [float(request.POST.get(f'grade_{i}', 0)) for i in range(1, 4) if request.POST.get(f'grade_{i}')]
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
'''
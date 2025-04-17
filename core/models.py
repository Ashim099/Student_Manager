from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    ROLES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLES, default='student')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"OTP for {self.user.email}: {self.otp}"

class Program(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_programs')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Module(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='modules')
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='taught_modules')

    def __str__(self):
        return f"{self.code} - {self.name}"

class StudentProgram(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrolled_programs')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='enrolled_students')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.program.name}"

class Resource(models.Model):
    title = models.CharField(max_length=100)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='resources')    
    file = models.FileField(upload_to='resources/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_resources')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Assignment(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='assignments')
    due_date = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_assignments')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Submission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='submissions/')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"

class Result(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='results')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='results')
    grade = models.FloatField()
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='published_results')
    published_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.module.code}: {self.grade}"

class Reminder(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminders')  # Renamed from 'user' to 'student'
    reminder_date = models.DateTimeField()  # Renamed from 'due_date'
    is_notified = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class Announcement(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='announcements')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='announcements')  # Added field
    created_at = models.DateTimeField(auto_now_add=True)  # Added field

    def __str__(self):
        return self.title
